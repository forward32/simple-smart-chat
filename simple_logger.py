def log(msg, filename):
    """
    This function writes string msg in file with name filename.
    Mode - a - writes in the end of file.
    """
    f = open(filename,"a")
    if (f):
        f.write(msg+"\n")
        f.close()
    else:
        print("Operation failed.")
