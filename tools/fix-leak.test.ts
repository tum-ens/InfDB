import { revokeToken, rotateToken, cleanGitHistory, addToGitignore } from './fix-leak';
import axios from 'axios';
import * as child_process from 'child_process';
import * as fs from 'fs';

jest.mock('axios');
jest.mock('child_process');
jest.mock('fs');
const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockExecSync = child_process.execSync as jest.Mock;
const mockFs = fs as jest.Mocked<typeof fs>;

beforeEach(() => {
    jest.clearAllMocks();
});

describe('revokeToken', () => {
    const token = 'glpat-1234567890abcdef';
    const gitlabUrl = 'https://gitlab.com/api/v4/personal_access_tokens/self';

    it('should call the GitLab API to revoke the token', async () => {
        mockedAxios.delete.mockResolvedValueOnce({ status: 204 });

        await revokeToken(token);

        expect(mockedAxios.delete).toHaveBeenCalledWith(
            gitlabUrl,
            {
                headers: { 'PRIVATE-TOKEN': token }
            }
        );
    });

    it('should resolve when revoke succeeds with status 204', async () => {
        mockedAxios.delete.mockResolvedValueOnce({ status: 204 });

        await expect(revokeToken(token)).resolves.toBeUndefined();
    });

    it('should throw if API returns non-204 status', async () => {
        mockedAxios.delete.mockResolvedValueOnce({ status: 403, data: { error: 'Forbidden' } });

        await expect(revokeToken(token)).rejects.toThrow('GitLab API returned status 403');
    });

    it('should throw on network error', async () => {
        mockedAxios.delete.mockRejectedValueOnce(new Error('Network error'));

        await expect(revokeToken(token)).rejects.toThrow('Network error');
    });
});

describe('rotateToken', () => {
    const oldToken = 'glpat-oldtoken';
    const newToken = 'glpat-newtoken12345';
    const gitlabUrl = 'https://gitlab.com/api/v4/personal_access_tokens';

    it('should create a new token and return it', async () => {
        mockedAxios.post.mockResolvedValueOnce({
            status: 201,
            data: { token: newToken, id: 42 }
        });

        const result = await rotateToken(oldToken, { name: 'new-token', scopes: ['api', 'read_repository'] });

        expect(mockedAxios.post).toHaveBeenCalledWith(
            gitlabUrl,
            { name: 'new-token', scopes: ['api', 'read_repository'] },
            { headers: { 'PRIVATE-TOKEN': oldToken } }
        );
        expect(result).toBe(newToken);
    });

    it('should throw if token creation fails', async () => {
        mockedAxios.post.mockRejectedValueOnce(new Error('User not authorized'));

        await expect(rotateToken(oldToken, { name: 'test', scopes: ['api'] })).rejects.toThrow('User not authorized');
    });

    it('should throw if response status is not 201', async () => {
        mockedAxios.post.mockResolvedValueOnce({ status: 401 });

        await expect(rotateToken(oldToken, { name: 'test', scopes: ['api'] })).rejects.toThrow('GitLab API returned status 401');
    });
});

describe('cleanGitHistory', () => {
    it('should run git filter-repo to remove the file from history', () => {
        mockExecSync.mockReturnValueOnce('');

        cleanGitHistory('tools/sunpot/.env');

        expect(mockExecSync).toHaveBeenCalledWith(
            'git filter-repo --invert-paths --path tools/sunpot/.env --force',
            { stdio: 'inherit' }
        );
    });

    it('should throw if git filter-repo fails', () => {
        mockExecSync.mockImplementationOnce(() => {
            throw new Error('filter-repo: no commits to rewrite');
        });

        expect(() => cleanGitHistory('tools/sunpot/.env')).toThrow('Failed to clean git history: filter-repo: no commits to rewrite');
    });

    it('should handle errors from execSync gracefully', () => {
        mockExecSync.mockImplementationOnce(() => {
            throw new Error('Command not found: git-filter-repo');
        });

        expect(() => cleanGitHistory('tools/sunpot/.env')).toThrow('Failed to clean git history: Command not found: git-filter-repo');
    });
});

describe('addToGitignore', () => {
    const globalGitignorePath = '.gitignore';
    const localModuleGitignorePath = 'tools/sunpot/.gitignore';

    afterEach(() => {
        jest.resetAllMocks();
    });

    it('should add entry to root .gitignore if file does not contain it', () => {
        mockFs.existsSync.mockReturnValueOnce(true);
        mockFs.readFileSync.mockReturnValueOnce('# some content\n');
        mockFs.appendFileSync.mockImplementationOnce(() => {});

        addToGitignore('tools/sunpot/.env', globalGitignorePath);

        expect(mockFs.readFileSync).toHaveBeenCalledWith(globalGitignorePath, 'utf-8');
        expect(mockFs.appendFileSync).toHaveBeenCalledWith(globalGitignorePath, '\ntools/sunpot/.env', 'utf-8');
    });

    it('should not append if entry already present', () => {
        mockFs.existsSync.mockReturnValueOnce(true);
        mockFs.readFileSync.mockReturnValueOnce('tools/sunpot/.env\n');

        addToGitignore('tools/sunpot/.env', globalGitignorePath);

        expect(mockFs.appendFileSync).not.toHaveBeenCalled();
    });

    it('should create .gitignore file if it does not exist', () => {
        mockFs.existsSync.mockReturnValueOnce(false);
        mockFs.writeFileSync.mockImplementationOnce(() => {});

        addToGitignore('tools/sunpot/.env', globalGitignorePath);

        expect(mockFs.writeFileSync).toHaveBeenCalledWith(globalGitignorePath, 'tools/sunpot/.env\n', 'utf-8');
    });

    it('should also add to module-level .gitignore if it exists', () => {
        mockFs.existsSync
            .mockReturnValueOnce(true)   // root exists
            .mockReturnValueOnce(true);  // module exists
        mockFs.readFileSync
            .mockReturnValueOnce('# root\n')
            .mockReturnValueOnce('# module\n');

        addToGitignore('tools/sunpot/.env', globalGitignorePath, localModuleGitignorePath);

        expect(mockFs.appendFileSync).toHaveBeenCalledWith(globalGitignorePath, '\ntools/sunpot/.env', 'utf-8');
        expect(mockFs.appendFileSync).toHaveBeenCalledWith(localModuleGitignorePath, '\ntools/sunpot/.env', 'utf-8');
    });

    it('should throw if readFile fails', () => {
        mockFs.existsSync.mockReturnValueOnce(true);
        mockFs.readFileSync.mockImplementationOnce(() => {
            throw new Error('Permission denied');
        });

        expect(() => addToGitignore('tools/sunpot/.env', globalGitignorePath)).toThrow('Failed to update .gitignore: Permission denied');
    });
});

describe('Integration: rotate and revoke flow', () => {
    it('should revoke old token after successful rotation', async () => {
        const oldToken = 'glpat-old';
        const newToken = 'glpat-new';
        mockedAxios.post.mockResolvedValueOnce({ status: 201, data: { token: newToken } });
        mockedAxios.delete.mockResolvedValueOnce({ status: 204 });

        const rotated = await rotateToken(oldToken, { name: 'rotated', scopes: ['api'] });
        await revokeToken(oldToken);

        expect(rotated).toBe(newToken);
        expect(mockedAxios.post).toHaveBeenCalledTimes(1);
        expect(mockedAxios.delete).toHaveBeenCalledTimes(1);
    });
});