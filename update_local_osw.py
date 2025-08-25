from osw.express import OswExpress

dependencies = {
    "File": "Category:OSW11a53cdfbdc24524bf8ac435cbf65d9d",
    "WikiFile": "Category:OSW11a53cdfbdc24524bf8ac435cbf65d9d",
    "LocalFile": "Category:OSW3e3f5dd4f71842fbb8f270e511af8031",
    "RGBValue": "Category:OSW7e33b78c2f154ebc845699b17009692c",
    "PseudoColoredLiquid": "Category:OSW50daf688f7694863a0e319a0a978079f",
    "PseudoColorMixing": "Category:OSW25e748d2fa7a4b19a6a74e0b7f2d0211",
}

if __name__ == "__main__":
    osw_obj = OswExpress(
        domain="wiki-dev.open-semantic-lab.org",
    )
    osw_obj.install_dependencies(dependencies)







