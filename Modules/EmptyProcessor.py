class EmptyProcessor:
    """Placeholder processor to handle file changes when no module is loaded."""
    def __init__(self, file_list, start_index=0):
        self.file_list = file_list or []
        self.current_index = start_index
        self.current_file = self.file_list[start_index] if self.file_list else None
        print(f"EmptyProcessor initialized with file list: {self.file_list}")

    def set_current_index(self, index):
        """Update the current file based on the index."""
        if 0 <= index < len(self.file_list):
            self.current_index = index
            self.current_file = self.file_list[index]
            print(f"EmptyProcessor - Current file updated to: {self.current_file}")
        else:
            print(f"EmptyProcessor - Invalid index: {index}")

