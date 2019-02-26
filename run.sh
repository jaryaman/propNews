echo "Accessing News Service"
python get_articles.py global_prios/global_prios.csv > articles_with_keywords.csv
echo "Computing QALY scores from global priorities"
python score_articles.py priorities.csv articles_with_keywords.csv > ranked_articles.csv
