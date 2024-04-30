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

     public_key = None
     private_key = None


     #constructor
     def __init__(self):
         
         #generate a prime number >512 bits for q and p
         self.q = number.getPrime(5)
         self.p = number.getPrime(5)
         self.n = self.p * self.q
         self.public_key = self.generatePublicKey()
         self.private_key = self.generatePrivateKey()
                

     def generatePublicKey(self):
         self.phi = (self.p-1)*(self.q-1)
         self.e = np.random.randint(2, self.phi-1)
         while np.gcd(self.phi, self.e) != 1:
                self.e = np.random.randint(2, self.phi-1)
         return PublicKey(self.e, self.n)
        
     
     def generatePrivateKey(self):
         d = self.phi
         while((d*self.e)%(self.phi) != 1):
            d = d + 1
         self.d = d
         return PrivateKey(self.p, self.q, self.d)

def RSAEncryption(p, public_key):
     c = (ord(p)**public_key.e)%public_key.n
     return c

def RSADecryption(c, private_key):
     p = (ord(c)**private_key.d)%(private_key.p*private_key.q)
     return p
  
     
#function to find the lowest common multple of two numbers
def TotientFunction( q, p):
     #check if q is greater than p
     #if true start with q and use to incriment
     if(q>p):
         x = q
         largest = q
     #if p is greater than q
     #start with p and use to incriment
     else:
         x= p
         largest = p
     #keep increasing potential common multiples until divisble by both q and p
     while((x%p != 0) or (x%q != 0)):
         #incirment potential common multiple by the largest value
         x += largest
      
     return x
       
     
class PublicKey:
    
     e = None
     n = None

    #constructor
     def __init__(self, e, n):
         self.e = e
         self.n = n
 
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
    #create empty ciphertext string
     plaintext = ""
     #iterate over each character in the message
     for c in message:
         #encrypt the character and append to ciphertext string
         plaintext = plaintext + chr(RSADecryption(c, private_key))
     #return complete ciphertext string
     return plaintext

