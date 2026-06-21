The `image_stego` module is designed to embed an input stream (`data_in`) into an image (`img_in`) based on the number of bits per pixel (`bpp`). However, the module exhibits unexpected behavior in the following scenario:

1. **No Embedding for `bpp=2'b10` and `bpp=2'b11`**  
   - When `bpp=10` or `bpp=11`, the output `img_out` remains identical to `img_in`, rather than embedding more bits from `data_in`.

---

## **Test Case Details**

Below are the relevant test vectors showing **Expected vs. Actual** outputs.

### **TC 1: `bpp = 2'b00`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00000001000000010000000100000001 | 00000001000000010000000100000001 |

### **TC 2: `bpp = 2'b01`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 0000000000001111 | 00000000000000000000001100000011 | 00000000000000000000001100000011 |

### **TC 3: `bpp = 2'b10`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00000111000001110000011100000111 | 00000001000000010000000100000001 |

### **TC 4: `bpp = 2'b11`**

| img_in                           | data_in          |         Expected img_out         |          Actual img_out          |
|----------------------------------|------------------|:--------------------------------:|:--------------------------------:|
| 00000001000000010000000100000001 | 1111111111111111 | 00001111000011110000111100001111 | 00000001000000010000000100000001 |

---

## **Summary of Issues**

- For `bpp=00` and `bpp=01`, the embedding works correctly.
- For `bpp=10` and `bpp=11`, the output simply passes through `img_in` without embedding any new bits from `data_in`.

---

**Identify and fix** the portion of the RTL logic that causes the output to ignore `data_in` when `bpp=10` or `bpp=11`. 
Ensure that:
1. **`bpp=2'b10`** properly embeds the corresponding bits from `data_in`.
2. **`bpp=2'b11`** also embeds the intended (higher) number of bits from `data_in`.
