# Ad-hoc markup fixers for preprocess


def merge_mi(start, name: str) -> None:
    if start.text != name[0]:
        return

    # check match and gathering garbage elements to delete
    cur = start
    garbages = []
    for c in name[1:]:
        # Note: next1: invisible times, next2: char
        if cur.getnext() is None or cur.getnext().getnext() is None:
            return

        if cur.getnext().getnext().text != c:
            return

        garbages += [cur.getnext(), cur.getnext().getnext()]
        cur = cur.getnext().getnext()

    # merge
    start.text = name
    parent = start.getparent()
    for g in garbages:
        parent.remove(g)


def fix1808_02342(root):
    for e in root.xpath('//mtext'):
        if e.text == 'E':
            e.tag = 'mi'
            e.attrib['mathvariant'] = 'normal'

        if e.text == 'KL':
            e.tag = 'mi'

        if e.text.strip() == 'maximize':
            e.tag = 'mi'
            e.text = e.text.strip()

        if e.text == 'arg':
            # add "arg" to max/min
            mm = e.getnext().getnext().xpath(
                './/mi[text()="max"]|.//mi[text()="min"]')[0]
            mm.text = 'arg' + mm.text

            # remove unnecessary elements
            e.getparent().remove(e)

    for e in root.xpath('//mo'):
        if e.text == '𝜃':
            e.tag = 'mi'
            e.text = 'θ'  # GREEK SMALL LETTER THETA

        if e.text == '𝑞':
            e.tag = 'mi'
            e.text = 'q'  # LATIN SMALL LETTER Q

    for e in root.xpath('//mi'):
        if e.text == 'old':
            e.tag = 'mtext'


def fix1711_09576(root):
    from lxml.html.builder import IMG

    for e in root.xpath('//mi'):
        merge_mi(e, 'ref')
        merge_mi(e, 'Acc')
        merge_mi(e, 'Rej')
        merge_mi(e, 'Im')

    for e in root.xpath('//figure[@class="ltx_figure"]'):
        # remove embed figures
        for c in e:
            if c.tag != 'img' and c.tag != 'figcaption':
                e.remove(c)

        # add <img>
        if [c.tag for c in e] == ['figcaption']:
            img = IMG()
            src = '/static/img/1711.09576/{}.png'.format(
                e.attrib['id'].replace('.', '_'))
            img.attrib['src'] = src
            img.attrib['alt'] = src
            e.insert(0, img)

    for e in root.xpath('//figure[@class="ltx_table"]'):
        # remove embed tables
        for c in e:
            if c.tag != 'figcaption':
                e.remove(c)

        # add <img>
        img = IMG()
        src = '/static/img/1711.09576/{}.png'.format(
            e.attrib['id'].replace('.', '_'))
        img.attrib['src'] = src
        img.attrib['alt'] = src
        e.insert(0, img)
