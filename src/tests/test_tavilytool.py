import pytest

from src.tools.tavily_tool import tavily_search
import re

class TestTavily:
    def test_tavily_search_maintains_threshold(self,):
        # set threshold
        threshold_=0.7
        #run search
        ret = tavily_search(
            query = "name the capitals of the top ten countries according to their gdp",
            threshold=threshold_,
            snippet_len=300,
            max_results=10
        )

        # extract score
        regex_score = re.compile(r"score:(\d+.?\d+\s?)")
        scores = regex_score.findall(ret)

        # cleanup and filter for scores above threshold
        new_scores = list(
                        filter(lambda x: x>threshold_,
                            [float(i.strip()) for i in scores]
                            )   
                        )

        # asserts
        assert len(new_scores)==len(scores),"Threshold is not being maintained"
        assert isinstance(ret,str)

