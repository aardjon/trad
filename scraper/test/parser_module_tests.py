import os
import pandas as pd
from parser_module import parse_post, parse_posts, parse_rating, parse_user_name, parse_page


def test_parse_post():
    test_dict = {
        0: {
            0: "Benutzer",
            1: "Ruth Madden|Wohnort: Zioncester|||23.11.2023 14:12",
            2: "Brenda Hutchinson|||04.07.2021 09:27",
            3: "Kenneth Mcintyre|Authentifizierter Benutzer|Wohnort: auf Asylsuche|||03.11.2018 16:31",
            4: "Abraham Castro|Wohnort: Abilene|||18.05.2009 11:54",
            5: "Carter Perez|||02.04.2008 20:47",
            6: "Althea Goodwin|Authentifizierter Benutzer|Wohnort: West Zolaville|||08.02.2008 11:10",
            7: "Wing William|Authentifizierter Benutzer|||30.10.2007 12:21",
            8: "Alice Chaney|Moderator|Authentifizierter Benutzer|||22.11.2007 15:04",
            9: "Kay Säller|Authentifizierter Benutzer|Wohnort: North Gracie|||27.05.2001 19:07",
            10: "Anthony Calhoun|||22.04.2001 11:22",
            11: "Claire Cline|Authentifizierter Benutzer|||24.04.2001 14:32",
            12: "Kuame Vinson|Co-Administrator|Authentifizierter Benutzer|||25.01.2001 13:43",
            13: "Ebony Edwards|Webmaster|Authentifizierter Benutzer|Wohnort: Fort Kallie|||02.10.2000 19:13",
            14: "Yeo Lambert|Authentifizierter Benutzer|Wohnort: http://example.com|||23.08.2000 15:01",
        },
        1: {
            0: "Kommentar",
            1: "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam.",
            2: "Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et.",
            3: "Sed ut perspiciatis unde omnis.",
            4: "Natus error sit voluptatem accusantium doloremque laudantium, totam rem.",
            5: "Li Europan lingues es membres del sam familie. Lor separat existentie es un myth.",
            6: "Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?",
            7: "Et harum quidem rerum facilis est et expedita distinctio.",
            8: "Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere.",
            9: "In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo.",
            10: "Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur.",
            11: "Vel illum qui dolorem eum fugiat quo voluptas nulla pariatur.",
            12: "Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi.",
            13: "Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo.",
            14: "Sed consequat, leo eget bibendum sodales, augue velit cursus nunc.",
        },
        2: {
            0: "Bewertung",
            1: "(Normal)",
            2: "+++ (Herausragend)",
            3: "+ (gut)",
            4: "+++ (Herausragend)",
            5: "++ (sehr gut)",
            6: "(Normal)",
            7: "++ (sehr gut)",
            8: "++ (sehr gut)",
            9: "++ (sehr gut)",
            10: "++ (sehr gut)",
            11: "+ (gut)",
            12: "+++ (Herausragend)",
            13: "+++ (Herausragend)",
            14: "+++ (Herausragend)",
        },
    }

    df = pd.DataFrame.from_dict(test_dict)

    # Parse single post
    print("Parse single Post:")
    print(parse_post(df.loc[2]))
    print("")

    # Parse post table
    print("Parse post table")
    result = parse_posts(df)
    print(len(result))
    print(result[0])


def test_parse_rating():
    print(parse_rating("--- (Kamikaze)"))
    print(parse_rating("-- (sehr schlecht)"))
    print(parse_rating("- (schlecht)"))
    print(parse_rating("(Normal)"))
    print(parse_rating("+ (gut)"))
    print(parse_rating("++ (sehr gut)"))
    print(parse_rating("+++ (Herausragend)"))


def test_parse_user():
    test_strings = [
        "Ruth Madden|Wohnort: Zioncester|||23.11.2023 14:12",
        "Brenda Hutchinson|||04.07.2021 09:27",
        "Kenneth Mcintyre|Authentifizierter Benutzer|Wohnort: auf Asylsuche|||03.11.2018 16:31",
        "Abraham Castro|Wohnort: Abilene|||18.05.2009 11:54",
        "Carter Perez|||02.04.2008 20:47",
        "Althea Goodwin|Authentifizierter Benutzer|Wohnort: West Zolaville|||08.02.2008 11:10",
        "Wing William|Authentifizierter Benutzer|||30.10.2007 12:21",
        "Alice Chaney|Moderator|Authentifizierter Benutzer|||22.11.2007 15:04",
        "Kay Säller|Authentifizierter Benutzer|Wohnort: North Gracie|||27.05.2001 19:07",
        "Anthony Calhoun|||22.04.2001 11:22",
        "Claire Cline|Authentifizierter Benutzer|||24.04.2001 14:32",
        "Kuame Vinson|Co-Administrator|Authentifizierter Benutzer|||25.01.2001 13:43",
        "Ebony Edwards|Webmaster|Authentifizierter Benutzer|Wohnort: Fort Kallie|||02.10.2000 19:13",
        "Yeo Lambert|Authentifizierter Benutzer|Wohnort: http://example.com|||23.08.2000 15:01",
    ]

    for test_string in test_strings:
        result = parse_user_name(test_string)
        print("Name: {}, Date: {}".format(result[0], result[1]))


def test_parse_page():
    dir_name = os.path.dirname(__file__)
    file = open(os.path.join(dir_name, "..", "test-data/sample1.html"), mode="r")
    page_text = file.read()
    file.close()
    page_data = parse_page(page_text)
    print(page_data)


if __name__ == "__main__":
    # test_parse_post()
    # test_parse_rating()
    # test_parse_user()
    test_parse_page()
