import random

while True:
    x = input("1-Son topaman(1-100)\n2-Son topasiz\nJavob: ")
    if x == '1':
        average = 52
        trials = 1
        while True:
            response = input(f"Siz o'ylagan son {average} (Y, N)")
            if response == 'Y':
                print(f"Men siz o'ylagan sonni {trials} urinishda topdim")
                break
            elif response == 'N':
                average = average // 2
            trials += 1
            
    elif x == '2':
        son = random.randint(1, 100)
        trials = 1
        while True:
            response = int(input("O'ylagan sonimni kiriting: "))
            if response == son:
                print(f"Siz men o'ylagan sonni {trials} urunishda topdingiz")
                break
            else:
                if response > son:
                    print("Men o'ylagan son kichikroq, Yana bir bor o'ylab ko'ring")
                elif response < son:
                    print("Men o'ylagan son kattaroq, yana bir bor o'ylab ko'ring")
            trials += 1
    else:
        break
        
            
        
