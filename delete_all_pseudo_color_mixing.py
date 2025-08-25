## script to clear the pseudo_color_mixing database

from osw.core import OSW
from osw.express import OswExpress
from osw.core import WtSite

if __name__ == "__main__":
    osw_obj = OswExpress(# domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
    )


    pseudo_color_mixing_ids = osw_obj.site.semantic_search("[[Category:OSW25e748d2fa7a4b19a6a74e0b7f2d0211]]") ##
    # PseudoColorMixing
    pseudo_colored_liquid_ids = osw_obj.site.semantic_search("[[Category:OSW50daf688f7694863a0e319a0a978079f]]")
    ###PseudoColoredLiquid

    ## query for all PseudoColoredLiquid instances to get their images
    query = """[[Category:OSW50daf688f7694863a0e319a0a978079f]]
        |?HasImage=image_id"""
    res = osw_obj.mw_site.api("ask", query=query, format="json", limit=1000)
    print(res)

    res_dict = res["query"]["results"]
    image_ids = []
    for liquid_id, sub_dict in res_dict.items():
        for image_id_dict in sub_dict["printouts"]["image_id"]:
            image_ids.append(image_id_dict["fulltext"])

    print("image_ids", image_ids)

    ## delete all items and ids:
    delete_ids = image_ids + pseudo_color_mixing_ids + pseudo_colored_liquid_ids

    delete_entities_download = osw_obj.load_entity(OSW.LoadEntityParam(titles = delete_ids))

    ## delete all entities
    osw_obj.delete_entity(delete_entities_download.entities)

    print("done")