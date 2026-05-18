$ cd /tmp/InfDB-mirror
$ git clone --bare https://github.com/tum-ens/InfDB.git
$ cd InfDB.git
$ git filter-repo \
    --path tools/sunpot/.env \
    --invert-paths \
    --force