The `caesar_cipher` module shifts each character of an `input_phrase` using per-character shift values from `key_phrase`, supporting **encryption** (`decrypt = 1'b0`) and **decryption** (`decrypt = 1'b1`). However, the module exhibits **unexpected behavior** under certain conditions due to the following issues:

1. **Uppercase Encryption (Missing Wrap-Around)**  
   When encrypting uppercase letters (`"A"` … `"Z"`), any shift beyond `'Z'` results in wrong characters.

2. **Uppercase Decryption (Wrong Direction)**  
   In decryption mode for uppercase letters, the shift key is **added** instead of being reversed, causing letters to move **further forward**.

3. **Non-Alphabetic Characters (Forced `+1` When Key=0)**  
   For characters outside `'A'..'Z'` or `'a'..'z'`, if the associated key is `0`, the module **increments** these characters by **1**, resulting in unintended transformations when no shift is expected.


---

## **Test Case Details**

Below are **three key test scenarios** that highlight each bug. For each test, the module is in **encryption** mode (if stated) or **decryption** mode, and we compare the **expected** vs. **actual** output to pinpoint the issues.

### **TC 1: Uppercase Encryption Wrap-Around**

| Mode    | Input Phrase | Key | Expected Output | Actual Output |
|---------|:------------:|:---:|:---------------:|:-------------:|
| Encrypt | XYZ          | 5   | CDE             | ]^_           |

---

### **TC 2: Uppercase Decryption in Wrong Direction**

| Mode    | Input Phrase (encrypted) | Key | Expected Output |     Actual Output     |
|---------|:------------------------:|:---:|:---------------:|:---------------------:|
| Decrypt | CDE                      | 5   | XYZ             | KLM (shifted forward) |
---

### **TC 3: Non-Alphabetic Characters with Zero Key**

| Mode    | Input Phrase |      Key      |        Expected Output       |       Actual Output      |
|---------|:------------:|:-------------:|:----------------------------:|:------------------------:|
| Encrypt | a1!@z        | 3, 1, 0, 0, 5 | d2!@e (or no shift if key=0) | d0"Ae (extra increments) |


---

Identify and fix these RTL Bugs to ensure the module behaves as expected in all scenarios.
