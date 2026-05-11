def encode_file_type(filename):
    if filename.endswith(".txt"):
        return 0
    elif filename.endswith(".jpg") or filename.endswith(".png"):
        return 1
    elif filename.endswith(".pdf"):
        return 2
    else:
        return 3