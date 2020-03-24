import logging
from lxml import etree
import re
from urllib.parse import quote

import namespace

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def encode(s):
    ret = s.translate(
        str.maketrans(
            {
                "(": "_",  # '%28',
                ")": "_",  # '%29',
                "（": "_",
                "）": "_",
                " ": "_",  # '%20',
                "/": "_",  # '%2F',
                "％": quote("％"),
                '"': quote('"'),
                "'": quote("'"),
                ",": quote(","),
                "#": quote("#"),
                "[": quote("["),
                "]": quote("]"),
                "<": quote("<"),
                ">": quote(">"),
            }
        )
    )
    ret = re.sub(r"_$", "", ret)
    return ret


def is_prefixed(term):
    for prefix in namespace.prefixes.keys():
        if term.startswith(f"{prefix}:"):
            return True
    return False


def to_rdf_term(term, prepend=""):
    if is_prefixed(term):
        if prepend:
            parts = term.split(":")
            term = f"{parts[0]}:{prepend}{encode(parts[1])}"
        else:
            term = encode(term)
    else:
        term = f":{prepend}{encode(term)}"
    return term


def convert(infile):
    tree = etree.parse(infile).getroot()
    # print(etree.tostring(tree))

    for ns, iri in namespace.prefixes.items():
        print(f"@prefix {ns}: <{iri}> .")
    default_prefixes = (
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        + "@prefix owl: <http://www.w3.org/2002/07/owl#> ."
    )
    print(default_prefixes + "\n")

    # W_CONCEPTS
    for el in tree.iterfind("./W_CONCEPTS/ISA"):
        # print(el.get("id"))

        parent = el.get("parent")
        parent = to_rdf_term(parent)

        child = el.get("child")
        child = to_rdf_term(child)

        triple = (child, "rdfs:subClassOf", parent)
        logger.debug(triple)
        print("{}\t{}\t{} .".format(*triple))

    cid_to_name = {}
    name_to_cid = {}

    ranges = set()  # Debug

    for el in tree.iterfind("./W_CONCEPTS/CONCEPT"):
        cid = el.get("id")
        label = el.findtext("./LABEL")
        name = to_rdf_term(label)
        cid_to_name[cid] = name
        name_to_cid[name] = cid

        ## LABEL
        t_label = (name, "rdfs:label", label.replace('"', '\\"'))
        logger.debug(t_label)
        print('{}\t{}\t"{}" .'.format(*t_label))

        ## DEF
        def_text = el.findtext("./DEF")
        if not def_text:
            continue
        def_text = def_text.replace('"', '\\"')
        t_def = (name, "rdfs:comment", def_text)
        logger.debug(t_def)
        print('{}\t{}\t"{}" .'.format(*t_def))

        ## SLOT
        for slot_el in el.iterfind("./SLOTS/SLOT"):
            role = slot_el.get("role")
            class_constraint = slot_el.get("class_constraint")
            assert role and class_constraint

            role = to_rdf_term(role, prepend="has_")

            constraints = [x.strip() for x in class_constraint.split("|")]

            # Limitation
            constraints = [re.sub(r"\[.*?(\]|\))$", r"", c) for c in constraints]
            constraints = [
                c for c in constraints if not (c.startswith("#") or c.startswith("p-"))
            ]

            constraints = [to_rdf_term(c) for c in constraints]

            if len(constraints) == 0:
                continue

            value = slot_el.get("value")

            # if value:
            #     if not constraints[0] == "string":
            #         continue  # Skip
            #     value = value.replace('"', '\\"')
            #     logger.debug("{} {}".format(role, value))
            #     t = (name, role, value)
            #     print('{}\t{}\t"{}" .'.format(*t))

            if value:
                # TODO: Fix
                if not constraints[0] == "yamato:string":
                    continue  # Skip
                value = value.replace('"', '\\"')
                logger.debug("{} {}".format(role, value))
                t = (name, role, value)
                print(
                    (
                        "{} rdfs:subClassOf\n"
                        + "[ a owl:Restriction ;\n"
                        + "  owl:onProperty {} ;\n"
                        + '  owl:hasValue "{}"\n'
                        + "] ."
                    )
                    .format(*t)
                    .replace("\n", "\t")
                )
            else:
                for c in constraints:
                    ranges.add(c)
                if len(constraints) == 1:
                    constraint = constraints[0]
                    t = (name, role, constraint)
                    print(
                        (
                            "{} rdfs:subClassOf"
                            + "  [ a owl:Restriction ;"
                            + "    owl:onProperty {} ;"
                            + "    owl:someValuesFrom {}"
                            + "  ] ."
                        ).format(name, role, constraint)
                    )
                else:
                    print(
                        (
                            "{} rdfs:subClassOf"
                            + "  [ a owl:Restriction ;"
                            + "    owl:onProperty {} ;"
                            + "    owl:someValuesFrom [ owl:unionOf ({}) ]"
                            + "  ] ."
                        ).format(name, role, " ".join(constraints))
                    )

    # for c in sorted(list(ranges)):
    #     logger.info("{}".format(c))

    # R_CONCEPTS
    prop_added = {}

    for el in tree.iterfind("./R_CONCEPTS/ISA"):
        # print(el.get("id"))
        parent = el.get("parent")
        child = el.get("child")
        assert parent is not None and child is not None

        parent = to_rdf_term(parent, prepend="has_")
        child = to_rdf_term(child, prepend="has_")

        if parent not in prop_added:
            print("{}\ta\towl:ObjectProperty .".format(parent))
            prop_added[parent] = True
        if child not in prop_added:
            print("{}\ta\towl:ObjectProperty .".format(child))
            prop_added[child] = True
        triple = (child, "rdfs:subPropertyOf", parent)
        logger.debug(triple)
        print("{}\t{}\t{} .".format(*triple))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    # prefix, iri
    parser.add_argument(
        "infile", nargs="?", type=argparse.FileType("r"), help="Input file."
    )
    args = parser.parse_args()

    if args.infile:
        convert(args.infile)
