def build_keyword_graph(keywords, max_depth=1, reciprocity=False, weighted=True, jaccard=True, cutoff=float('inf')):
    """Returns a keyword graph extracted from the hyperlink structure from Wikipedia.
    
    Args:
        keywords: a list of str or str of the keywords whose corresponding Wikipedia articles are roots of graph crawling
        max_depth: an int or float which imposes the depth of crawl from the root position; default 1
        reciprocity: if True then child nodes are added to the graph only if they link back to the parent; default False
        weighted: if True then the network's edges are weighted by the number of common links between parent and child node; default True
        jaccard: if True then the edge weights are normalised between 0 and 1 as in Jaccard's similarity index; default True
        cutoff: an int or float which imposes a size restriction on the network; default inf
        
    Returns:
        A dict object whose keys are node names and values are a tuple containing number of links of that node and a dict containing parent 
        names and the corresponding edge weights.
    """
    if not hasattr(keywords, '__iter__'): keywords = [keywords]
    import wikipedia as wk
    pgs = [wk.page(keyword) for keyword in keywords]
    network = dict([(pg.title, (pg.links, [])) for pg in pgs])
    queue = [(0, pg.title, pg.links) for pg in pgs]
    while len(queue)>0 and len(network)<cutoff:
        depth, parent, children = queue.pop(0)
        if depth >= max_depth: continue
        for child in children:
            if child not in network:
                try:
                    pg_curr = wk.page(child)
                    children_curr = pg_curr.links
                    if parent in children_curr or not reciprocity:
                        network[child] = (children_curr, [parent])
                        queue.append((depth+1, child, children_curr))
                except:
                    pass
            else:
                if parent in network[child][0] or not reciprocity:
                    network[child][1].append(parent)
            if len(network)>=cutoff: break
    
    if weighted:
        weighted_network = dict()
        for key, value in network.items():
            weighted_network[key] = (len(value[0]), {})
            for par in value[1]:
                weighted_network[key][1][par] = len([c for c in network[par][0] if c in value[0]])
                if jaccard: weighted_network[key][1][par] = weighted_network[key][1][par]/(len(value[0])+len(network[par][0])-weighted_network[key][1][par])
        return weighted_network
    else: return network

def sort_keywords(keyword_weighted_graph):
    keywords_dict = dict()
    for key, value in keyword_weighted_graph.items():
        for par, sim in value[1].items():
            if par in keywords_dict: keywords_dict[par].append((key, sim))
            else: keywords_dict[par] = [(key, sim)]
    
    for key, value in keywords_dict.items():
        keywords_dict[key] = sorted(value, key=lambda x: x[1], reverse=True)
    return keywords_dict

global_priorities = ['poverty', 'cancer', 'mental health', 'smoking', 'climate change', 'air pollution', 
                     'heart disease', 'tuberculosis', 'pneumonia', 'diarrhea', 'perinatal mortality', 'hiv', 
                     'asthma', 'diabetes']

gprios_keywords = build_keyword_graph(global_priorities)

import pickle
pickle.dump(gprios_keywords, open('global_prios/gprios_keywords_depth_1.pkl', 'wb'))

