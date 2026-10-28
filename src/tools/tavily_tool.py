from tavily import TavilyClient
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# client = TavilyClient(
#     api_key=os.getenv("TAVILY_API_KEY")
# )


load_dotenv()

@contextmanager
def tavily_client():
    client=None
    try:
        print("\n\n**using context manager**")
        client = TavilyClient(
            api_key=os.getenv("TAVILY_API_KEY")
        )
        yield client
    except Exception as e:
        print(f"error : {e}")
        raise 
    finally:
        print("cleaning up")
        if client is not None:
            client.close()


def tavily_search(query,threshold=0.7,snippet_len=300,max_results=5)-> str :


    with tavily_client() as client:
        response = client.search(
            query=query,
            max_results=max_results
        )

        results_ = []

        for i,result in enumerate(response.get("results",[]) ): 
            score=result.get("score",0)
            if score > threshold:
                url = result.get("url","")
                title = result.get("title","")
                snippet= result.get("content","")[:snippet_len]
                if snippet:
                    snippet+="..."
                results_.append(
                    (score,i,title,url,snippet)
                    )
        # sort the results_  and then print it out
        results_ = sorted(results_,reverse=True)

        results_ = [
            f"{i}.**{title}**\n{url}\n{snippet} \n score:{score}" for score,i,title,url,snippet in results_
        ]

        return "\n\n".join(results_)



if __name__=="__main__":
    
    ans = tavily_search("who let the dogs out?",snippet_len=40,threshold=0.8,max_results=20)
    print(ans)