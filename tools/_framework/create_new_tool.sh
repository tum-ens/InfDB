#!/bin/bash
# Set locale for consistent text processing
export LC_ALL=C
export LANG=C

# Check if a name argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: bash create_new_tool.sh <new-name>"
    echo "Example: bash create_new_tool.sh my-new-tool"
    exit 1
fi

NEW_NAME="$1"
# Convert new name to snake_case for file/variable names
SNAKE_CASE_NAME=$(echo "$NEW_NAME" | tr '-' '_')

SOURCE_DIR="$(dirname "$0")"
PARENT_DIR="$(dirname "$SOURCE_DIR")"
TARGET_DIR="$PARENT_DIR/$NEW_NAME"

# Check if target directory already exists
if [ -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR already exists"
    exit 1
fi

# Copy the template directory to the new name
echo "Copying _infdb-template to $NEW_NAME..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

# Replace all occurrences of "choose-a-name" with the new name
echo "Replacing placeholders with $NEW_NAME..."
find "$TARGET_DIR" -type f -exec sed -i.bak "s/choose-a-name/$NEW_NAME/g" {} +
find "$TARGET_DIR" -type f -exec sed -i.bak "s/choose_a_name/$SNAKE_CASE_NAME/g" {} +
find "$TARGET_DIR" -type f -name "*.bak" -delete

# Rename files that contain "choose-a-name" or "choose_a_name"
find "$TARGET_DIR" -depth -name "*choose-a-name*" -o -name "*choose_a_name*" | while read -r file; do
    new_file=$(echo "$file" | sed "s/choose-a-name/$NEW_NAME/g" | sed "s/choose_a_name/$SNAKE_CASE_NAME/g")
    mv "$file" "$new_file"
done

# Rename Readme.md to Readme-DevContainer.md
if [ -f "$TARGET_DIR/Readme.md" ]; then
    mv "$TARGET_DIR/Readme.md" "$TARGET_DIR/Readme-DevContainer.md"
fi
# Rename Readme_template.md to Readme.md
if [ -f "$TARGET_DIR/Readme_template.md" ]; then
    mv "$TARGET_DIR/Readme_template.md" "$TARGET_DIR/Readme.md"
fi

# Remove the create_new_tool.sh script from the new directory
if [ -f "$TARGET_DIR/create_new_tool.sh" ]; then
    rm "$TARGET_DIR/create_new_tool.sh"
fi

echo "Done! Created new tool at $TARGET_DIR"