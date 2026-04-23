#!/bin/bash
# Set locale for consistent text processing
export LC_ALL=C
export LANG=C

# Check if a name argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: bash rename.sh <new-name>"
    echo "Example: bash rename.sh my-new-tool"
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

# Replace all occurrences of "buildings-to-street" with the new name
echo "Replacing placeholders with $NEW_NAME..."
find "$TARGET_DIR" -type f -exec sed -i.bak "s/buildings-to-street/$NEW_NAME/g" {} +
find "$TARGET_DIR" -type f -exec sed -i.bak "s/buildings_to_street/$SNAKE_CASE_NAME/g" {} +
find "$TARGET_DIR" -type f -name "*.bak" -delete

# Rename files that contain "buildings-to-street" or "buildings_to_street"
find "$TARGET_DIR" -depth -name "*buildings-to-street*" -o -name "*buildings_to_street*" | while read -r file; do
    new_file=$(echo "$file" | sed "s/buildings-to-street/$NEW_NAME/g" | sed "s/buildings_to_street/$SNAKE_CASE_NAME/g")
    mv "$file" "$new_file"
done

# Remove the rename.sh script from the new directory
if [ -f "$TARGET_DIR/rename.sh" ]; then
    rm "$TARGET_DIR/rename.sh"
fi

echo "Done! Created new tool at $TARGET_DIR"