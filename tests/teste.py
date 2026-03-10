import bcrypt

password = "rossini135"

# i need to crypt with bcrypt the password and print
hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
print(hashed_password)