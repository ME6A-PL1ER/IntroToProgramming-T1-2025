def check_pass():
    attempt = input("GIMME PASS")
    actual = "password"
    if attempt == actual:
        print("access granted")
    else:
        print("access denied")
        check_pass()

check_pass()