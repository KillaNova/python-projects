my_name = "hamza"
my_age = 25
my_religion = "islam"
my_nationality = "Turkish"
my_gender = "male"
i_am_a_student = True
i_like_programming = True
I_am_a_teacher = False
hobbies = ["gym", "coding", "crypto", "gaming"]

print(
    "My name is",
    my_name,
    "I am",
    my_age,
    "I follow",
    my_religion,
    "I am",
    my_nationality,
)
print("I am a student:", i_am_a_student)
print(
    "programming is what I like, and that is: ",
    i_like_programming,
    "Have I mastered it?: ",
    I_am_a_teacher,
)

if my_age >= 18:
    print("I am an adult.")
elif my_age >= 13:
    print("I am a teenager.")
else:
    print("I am a child.")

if i_like_programming == True:
    print("i_like_programming")
else:
    print("False")

if i_am_a_student == False:
    print("Student does not like programming")
elif i_am_a_student == True:
    print("Likes programming")
else:
    print("Student does not understand logic")


for i in range(3):
    print(my_name)

for i in range(1, 11):
    print(i)

for hobbie in hobbies:
    print(hobbie)

for i in range(1):
    print(hobbies[1])


def greet(name):
    print(f"Salam, {name}!")


greet("Hamza")


def say_age(your_age):
    print(f"you are, {your_age}!")
    if your_age >= 18:
        print("Your are an Adult!")
    elif your_age >= 13:
        print("You are a Teenager!")
    else:
        print("You are Minor!")


say_age(25)


def add(a, b):
    antwoord = a + b
    print(antwoord)


add(7, 3)
