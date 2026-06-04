from nfcscript import *

def demo_ntag21x():
    init_nfc(hardware="serial", driver="pn532", port="COM20")

    bind_card("ntag21x")
    find_card()
    tag = get_active_tag()
    print(f"tag: {type(tag).__name__}, UID={tag.uid.hex(' ')}")

    version = get_version()
    print(f"get_version: {version.hex(' ')}")

    ASSERT(len(version), 8)


if __name__ == "__main__":
    demo_ntag21x()
