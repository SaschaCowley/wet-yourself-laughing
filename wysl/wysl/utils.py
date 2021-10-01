def elicit_int(prompt="",
               values=None,
               err="Invalid input, try again",
               default=None):
    i = None
    while i is None:
        try:
            i = input(prompt).strip()
            if i == "" and default is not None:
                i = default
            else:
                i = int(i)
            if i is not None and i not in values:
                raise ValueError
        except ValueError:
            print(err)
            i = None
    return i
