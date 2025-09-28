import blurhash_avif as bha

if __name__ == "__main__":
    avif_path = "/Users/cooper/Desktop/_DSC2512.avif"
    blurhash = bha.encode(avif_path)
    if blurhash:
        print(f"BlurHash: {blurhash}")
    else:
        print("Failed to generate BlurHash")
