from flask import Flask,request,jsonify
import requests
import xml.etree.ElementTree as ET
from google_play_scraper import app,reviews,Sort
import time

application=Flask(__name__)

def find_text(parent,path,ns):
    element=parent.find(path,ns)
    return element.text if element is not None else ""

def fetch_appstore_reviews(app_id,country,page):
    url=f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/xml"
    response=requests.get(url)
    root=ET.fromstring(response.content)
    ns={'a':'http://www.w3.org/2005/Atom',
        'im': 'http://itunes.apple.com/rss'}
    reviews=[]
    entries=root.findall('a:entry',ns)
    for entry in entries:
        review={
            "author":find_text(entry,'a:author/a:name',ns),
            "title":find_text(entry,'a:title',ns),
            "content":find_text(entry,'a:content',ns),
            "rating":find_text(entry,'im:rating',ns)
        }
        reviews.append(review)
    return reviews

def fetch_playstore_reviews(app_id,country):
    token=None
    seen_tokens=set()
    output=[]
    max=1000
    while len(output)<=max:
        results,token=reviews(
            app_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=100,
            continuation_token=token
        )
        if not token:
            output.append({"End":"All reviews have been displayed."})
            return output
        if token in seen_tokens:
            output.append({"Error":"Repeated token, exiting the program..."})
            return output
        seen_tokens.add(token)
        for result in results:
            output.append({"name":result['userName'],"rating":result['score'],"review":result['content']})
        time.sleep(2)
    return output

@application.route('/check_reviews',methods=["GET"])
def check_reviews():
    if request.is_json:
        info=request.get_json()
        app_id=info["app_id"]
        country=info["country"]
        if type(app_id) is int:
            max_pages=10
            total=[]
            for page in range(1,max_pages+1):
                reviews=fetch_appstore_reviews(app_id,country,page)
                total.extend(reviews)
            length=len(total)
            total.append({"Reviews retrieved":length})
            return jsonify(total)
        else:
            output=fetch_playstore_reviews(app_id,country)
            return jsonify(output)
            
    else:
        return jsonify({"Error":"Request must be in JSON."})

if __name__=="__main__":
    application.run()