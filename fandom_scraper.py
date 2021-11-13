import requests
from bs4 import BeautifulSoup
import codecs, json, os.path

class Character:
    def __init__(self, char_name, char_wiki, char_appearances=[]):
        self.name = char_name
        self.wiki = char_wiki
        if len(char_appearances) > 0:
            self.appearances = char_appearances
        else:
            self.appearances = []


def dump_to_d3_json(filename, characters, wiki_names):
    nodes = []
    links = []

    wiki_node_indices = {}

    # create nodes (characters/wikis)
    for i in range(len(characters)):
        index = i + 1
        character = characters[i]
        node = { 'id': index, 'name': character.name, 'type': 'character' }
        nodes.append(node)
    
    for i in range(len(wiki_names)):
        index = len(characters) + i + 1
        node = { 'id': index, 'name': wiki_names[i], 'type': 'wiki' }
        nodes.append(node)
        wiki_node_indices[wiki_names[i]] = index
    
    # create links (characters to wikis)
    for i in range(len(characters)):
        char_node_index = i + 1
        home_link = { 'source': char_node_index, 'target': wiki_node_indices[characters[i].wiki] }
        links.append(home_link)
        for wiki in characters[i].appearances:
            links.append({ 'source': char_node_index, 'target': wiki_node_indices[wiki] })

    # write out
    with codecs.open(filename, 'w', 'utf_8') as outfile:
        json.dump({'nodes' : nodes, 'links' : links}, outfile, indent=4)


def write_characters_to_file(filename, characters):
    with codecs.open(filename, 'w', 'utf_8') as char_file:
        for character in characters:
            char_file.write(f'{character.name},{character.wiki}')
            if len(character.appearances) > 0:
                char_file.write(',')
                for i in range(len(character.appearances) - 1):
                    char_file.write(character.appearances[i])
                    char_file.write(',')
                char_file.write(character.appearances[-1])
            char_file.write('\n')

def load_characters_from_file(filename):
    characters = []
    with codecs.open(filename, 'r', 'utf_8') as char_file:
        line = char_file.readline()
        while line:
            split_line = [ x.strip() for x in line.split(',') ]
            character = Character(split_line[0], split_line[1])
            if len(split_line) > 2:
                character.appearances = split_line[2:]
                if isinstance(character.appearances, list) and len(character.appearances) > 1:
                    character.appearances = list(set(character.appearances))

            characters.append(character)
            line = char_file.readline()
    return characters

def consolidate_characters(characters):
    # sort the list
    characters.sort(key=(lambda x: x.name.lower()))

    # consolidate duplicates
    characters_consolidated = []
    prev_matched = False
    for i in range(len(characters) - 1):
        if characters[i].name.lower() == characters[i+1].name.lower() and not characters[i+1].wiki == characters[i].wiki and characters[i+1].wiki not in characters[i].appearances and ' ' in characters[i].name:
                if not prev_matched:
                    # only add to the final list if this is a new name
                    characters_consolidated.append(characters[i])
                    prev_matched = True
                # add a duplicate to the appearances list
                characters_consolidated[-1].appearances.append(characters[i+1].wiki)

                print(f'Consolidated {characters[i].name} from {characters[i].wiki} with {characters[i+1].name} from {characters[i+1].wiki}')
        elif characters[i].name.lower() == characters[i+1].name.lower() and characters[i+1].wiki == characters[i].wiki:
            pass
        else:
            prev_matched = False
            characters_consolidated.append(characters[i])

    return characters_consolidated

if __name__ == '__main__':

    csv_filename = 'characters.csv'
    json_dump = 'graph.json'

    characters = load_characters_from_file('characters_raw.csv')
    characters = consolidate_characters(characters)
    write_characters_to_file(csv_filename, characters)
    exit()

    characters = []
    wiki_names = []

    # create new data via webscraping
    print('Webscraping...')
    num_pages_to_scrape = 100

    for page_no in range(num_pages_to_scrape):
        fandom_links = f'https://www.google.com/search?q=site%3A*.fandom.com%2Fwiki%2FCategory%3ACharacters&start={page_no * 50}&num={50}'

        resp = requests.get(fandom_links)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        all_links = soup.find_all('a')
        wiki_urls = [ x.get('href')[7:x.get('href').index('&sa=')] for x in all_links if '.fandom.com' in x.get('href') and '*.fandom.com' not in x.get('href') ]

        # wiki_urls has urls to a bunch of *.fandom.com whatevers

        for character_wiki in wiki_urls:
            wiki_name = character_wiki[len('https://'):character_wiki.index('.fandom.com')]
            wiki_names.append(wiki_name)
            soup = BeautifulSoup(requests.get(character_wiki).text, 'html.parser')
            character_pages = soup.find_all('a', class_='category-page__member-link')
            for link in character_pages:
                if ':' not in link['title']:
                    characters.append(Character(link['title'].replace(',', '-'), wiki_name))
                    print(link['title'])

    # write raw data
    print('Saving raw data...')
    write_characters_to_file('characters_raw.csv', characters)

    # consolidate
    print('Consolidating...')
    characters = consolidate_characters(characters)

    # save characters into a csv
    print('Saving consolidated data...')
    write_characters_to_file(csv_filename, characters)

    # dump to json
    print('Dumping consolidated data to JSON...')
    dump_to_d3_json(json_dump, characters, wiki_names)
