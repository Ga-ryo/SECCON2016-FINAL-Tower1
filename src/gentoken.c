// gcc -static -o gentoken gentoken.c -lcrypto -ldl
#include <openssl/hmac.h>
#include <openssl/evp.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <stdio.h>

int main(int argc, char **argv) {
    uint32_t now = (uint32_t)time(NULL);
    unsigned char *key = "9bhaLHnw4g9@#";
    unsigned char data[32];
    const unsigned char *hmac;
    unsigned char result[64];
    int nstones = atoi(argv[1]);
    int i=0;
    snprintf(data, sizeof(data), "%u|%u", now, nstones);
    hmac = HMAC(EVP_sha1(), key, strlen(key), data, strlen(data),
                NULL, NULL);

    snprintf(result, sizeof(result), "%08x%08x", now, nstones);
    for (i = 0; i < 20; i++) {
        snprintf(&result[i*2 + 16], sizeof(3), "%02x", hmac[i]);
    }
    printf("%s\n", result);
    return 0;
}
