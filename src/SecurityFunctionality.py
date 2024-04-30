#Requires import of pycr
from Crypto.Util import number
import numpy as np


class RSAKeys():
     
     #shared values generated for this particular connection
     q = None
     p = None
     n = None
     e = None
     d = None
     phi = None

    #class variables for the public and private keys
     public_key = None
     private_key = None


     #constructor
     def __init__(self):   
         #generate a prime number >512 bits for q and p
         self.q = number.getPrime(10)
         self.p = number.getPrime(10)
         #n = p*q
         self.n = self.p * self.q
         #call method to create public key object
         self.public_key = self.generatePublicKey()
         #call method to create private key object
         self.private_key = self.generatePrivateKey()
                
    #Generate a public key object with values for e and n
     def generatePublicKey(self):
         #e is a value must be > 1 & < (p-1)*(q-1)
         #calclulate (p-1)*(q-1) (phi)
         self.phi = (self.p-1)*(self.q-1)
         #generate a number from 2 to the maximum value of e
         self.e = np.random.randint(2, self.phi-1)
         #check if it satisfied requirements for e
         #must have a greatest common divisor = 1
         while np.gcd(self.phi, self.e) != 1:
                #if it doesnt satisfy the requirements then pick a new number
                self.e = np.random.randint(2, self.phi-1)
         return PublicKey(self.e, self.n)
        
     #Generate a private key object with values for p, q, & d
     def generatePrivateKey(self):
         #initialize d to (p-1)*(q-1)
         d = self.phi
         #keep looking for d while (de)mod(phi) = 1
         #both d and phi are coprime (1 is only common divisor)
         while((d*self.e)%(self.phi) != 1):
            #incriment d until correct value is found
            d = d + 1
        #set class variable
         self.d = d
         return PrivateKey(self.p, self.q, self.d)

#Function simulating encryption 
def RSAEncryption(p, public_key):
     #ciphertext = (p^e)mod(n)
     c = (ord(p)**public_key.e)%public_key.n
     return c

#Function simulating decryption
def RSADecryption(c, private_key):
     #plaintext = (c^d)mod(n)
     p = (ord(c)**private_key.d)%(private_key.p*private_key.q)
     return p
      
    
#create a public key class with e and n as values
class PublicKey:
    
     e = None
     n = None

    #constructor
     def __init__(self, e, n):
         self.e = e
         self.n = n
 
#Create a private key clas with p, q, d as values
class PrivateKey:
     p = None
     q = None
     d = None

     def __init__(self, p, q, d):
          self.p = p
          self.q = q
          self.d = d
        


def RSAEncode(message, public_key):
     #create empty ciphertext string
     ciphertext = ""
     #iterate over each character in the message
     for p in message:
         #encrypt the character and append to ciphertext string
         ciphertext = ciphertext + chr(RSAEncryption(p, public_key))
     #return complete ciphertext string
     return ciphertext

def RSADecode(message, private_key):
    #create empty plaintext string
     plaintext = ""
     #iterate over each character in the message
     for c in message:
         #encrypt the character and append to plaintext string
         plaintext = plaintext + chr(RSADecryption(c, private_key))
     #return complete plaintext string
     return plaintext
