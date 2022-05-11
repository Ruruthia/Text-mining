from collections import defaultdict

import editdistance

EXACT = [
    '../List_2/outputs/contents_exact_full_postinglists.txt',
    '../List_2/outputs/titles_exact_full_postinglists.txt',
]
LEMATIZED = [
    '../List_2/outputs/contents_lematized_full_postinglists.txt',
    '../List_2/outputs/titles_lematized_full_postinglists.txt'
]


def read_text(lines):
    content = []
    from_title = 0
    contents = []
    titles = []
    for line in lines:
        if "TITLE:" in line:
            from_title = 0
            title = line[7:]
            titles.append([title])
            if len(content) > 0:
                contents.append(content)
            content = []
        if len(line.strip()) > 0:
            content.append(line)
        from_title += 1
    if len(content) > 0:
        contents.append(content)
    return contents, titles


def find_word(word, paths):
    # find word in postinglists and return indexes of corresponding documents
    idxs = []
    for path in paths:
        with open(path, 'r') as file:
            idx = []
            for line in file:
                partitioned = line.partition(":")
                key = partitioned[0]
                if key == word:
                    idx = partitioned[2].split(", ")
                    idx = [int(w.strip()) for w in idx]
                    break
            idxs.append(idx)
    return idxs


def df(word):
    freq1 = find_word(word, EXACT)
    freq2 = find_word(word, LEMATIZED)
    return len(freq1[0]) + len(freq1[1]) + len(freq2[0]) + len(freq2[1])


def prepare_question(question, morph):
    # split and lematize question
    lematized_question = []
    analysis = morph.analyse(question)
    question = question.split(" ")
    question = [''.join(filter(str.isalnum, word.lower())) for word in question]
    for i, j, interp in analysis:
        lematized_question.append(interp[1].partition(":")[0])
    return lematized_question, question


def prepare_hits(question, morph):
    # return hits per word in question
    lematized_question, question = prepare_question(question, morph)
    exact_hits = []
    lematized_hits = []
    for word in question:
        exact_hits.append(find_word(word, EXACT))
    for word in lematized_question:
        lematized_hits.append(find_word(word, LEMATIZED))
    return exact_hits, lematized_hits


def count_hits(hits, candidates):
    # count hits per document
    contents_counts = defaultdict(int)
    titles_counts = defaultdict(int)
    for current_word_hits in hits:
        for article_idx in current_word_hits[0]:
            if len(candidates) > 0:
                if article_idx in candidates:
                    contents_counts[article_idx] += 1
            else:
                contents_counts[article_idx] += 1

        for article_idx in current_word_hits[1]:
            if len(candidates) > 0:
                if article_idx in candidates:
                    titles_counts[article_idx] += 1
            else:
                titles_counts[article_idx] += 1
    return contents_counts, titles_counts


def score_documents(question, weights, morph, candidates):
    exact_hits, lematized_hits = prepare_hits(question, morph)
    exact_contents_hits, exact_titles_hits = count_hits(exact_hits, candidates)
    lematized_contents_hits, lematized_titles_hits = count_hits(lematized_hits, candidates)
    all_hits = set(exact_contents_hits.keys()) | set(exact_titles_hits.keys()) | set(
        lematized_contents_hits.keys()) | set(lematized_titles_hits.keys())
    scores = {}
    for hit in all_hits:
        scores[hit] = weights[4] * 1 / (hit + 1)
        if hit in exact_titles_hits:
            scores[hit] += exact_titles_hits[hit] * weights[0]
        if hit in exact_contents_hits:
            scores[hit] += exact_contents_hits[hit] * weights[1]
        if hit in lematized_titles_hits:
            scores[hit] += lematized_titles_hits[hit] * weights[2]
        if hit in lematized_contents_hits:
            scores[hit] += lematized_contents_hits[hit] * weights[3]
    scores = {k: v for k, v in sorted(scores.items(), key=lambda item: -item[1])}
    return scores


def lematize_quote(quote, morph):
    analysis = morph.analyse(quote)
    current_idx = 0
    current_stemmed_quote = []
    for i, j, interp in analysis:
        if i == current_idx:
            current_stemmed_quote.append(interp[1].partition(":")[0])
            current_idx += 1
    current_stemmed_quote = [word for word in current_stemmed_quote if word.isalpha()]
    current_stemmed_quote = [word.lower() for word in current_stemmed_quote if len(word) > 3]
    return set(current_stemmed_quote), current_stemmed_quote


def scaled_editdist(ans, cor):
    ans = ans.lower()
    cor = cor.lower()

    return editdistance.eval(ans, cor) / len(cor)
