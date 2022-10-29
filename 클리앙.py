
from bs4 import BeautifulSoup
import requests

import time
from datetime import datetime

# 현재 CSV파일로 저장. 추후에 DB로 저장하게 되면 변경
import pandas as pd
from requests.models import Response, requote_uri
#import pymongo
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Crawler:
    def __init__(self):
        self.keyword = '오삼불고기' #수집 키워드
        self.site = '클리앙' # 수집 사이트
        self.url = 'https://www.clien.net/service/search?q={keyword}&sort=recency&p={page}&boardCd=&isBoard=false' # 수집할 게시물리스트(게시판) url (검색조건(keyword, site, startDate, endDate)에 따라 설정)
        self.postUrls = []  # 게시판에서 게시물 url들을 담아 리턴할 리스트

    # 데이터에서 html tag 제외
    def delrn(self, text):
        return text.replace("\t","").replace("\n","").replace("\r","").lstrip().rstrip()

    def getList(self)-> list:

        page = 0
        tester = None

        while True:
            print('[ * ] page -> '+ str(page) )
            req = requests.get(self.url.format(page=page,keyword=self.keyword))
            soup = BeautifulSoup(req.text, 'html.parser')
            postlist = soup.find('div',{'class':'contents_jirum'})

            tester1 = postlist.findAll('a',{'class':'subject_fixed'})[0]['href'].split('&p=')[0]
            if tester1 == tester:
                break

            for a in postlist.findAll('a',{'class':'subject_fixed'}):
                postInfor = {
                             'url': 'https://www.clien.net'+a['href'].split('&p=')[0],
                             'crawled':False, # getPost()에서 해당url에서 게시물 상세정보를 가져왔는지 확인할 플래그,
                            }

                exist = next((item for item in self.postUrls if item['url'] == postInfor['url']), None)
                if type(exist) != dict: self.postUrls.append(postInfor)
                else:
                    break

            tester = postlist.findAll('a',{'class':'subject_fixed'})[0]['href'].split('&p=')[0]
            page = page+1
        print('[ - ] lenPostUrls = ', len(self.postUrls))

    def getPost(self)-> list:
        # 게시물 상세정보 수집 
        for post in self.postUrls:
            req = requests.get(post['url'], verify=False)
            print('[ * ] post req -> '+post['url'])
            soup = BeautifulSoup(req.text, 'html.parser')
            postinfo = soup.find('h3',{'class':'post_subject'}).findAll('span')
            
            name = self.delrn(soup.find('span',{'class':'nickname'}).text)
            if name == "" : 
                name = str(soup.find('span',{'class':'nickname'}).find('img')['alt'])


            
            # --- 게시물의 제목/내용/작성자아이디/작성자닉네임/작성일자 등을 가져옴 <사이트마다 태그변경 또는 소스코드 수정 필요>
            post['title'] = postinfo[0].text
            post['Content'] = self.delrn(soup.find('div',{'class':'post_article'}).text)
            post['userid'] = soup.find('button',{'class':'button_report'})['onclick'].split("('")[1].split("')")[0]
            post['userip'] = soup.find('div',{'class':'post_author'}).findAll('span')[3].text
            post['username'] = name
            post['datePublished'] = self.delrn(soup.find('div',{'class':'post_author'}).findAll('span')[0].text).split(' 수정일')[0]
            post['dateScraped'] = datetime.now()

            # 이미지가 있다면
            post['img'] = []
            for img in soup.find('div',{'class':'post_article'}).findAll('img'):
                post['img'].append(img['src'])

            post['like'] = soup.find('a',{'class':'symph_count'}).find('strong').text
            # like(좋아요수) / hate(싫어요수) / reply(댓글수) / thumbnail(썸네일) 이 존재하면 수집

            # ---댓글을 수집해야하는 사이트면
            post['CmtCnt'] = None
            post['Comments'] = []

            #사이트마다 댓글 html형식에 따라 소스수정
            CommentList = soup.findAll('div',{'data-role':'comment-row'})
            cmtnum = 0
            replycounter = 0
            for n in CommentList:
                
                n = CommentList[cmtnum]
                name = self.delrn(n.find('span',{'class':'nickname'}).text)
                if name == "" : name = n.find('span',{'class':'nickname'}).find('img')['alt']

                # --- 댓글의 내용/작성자아이디/작성자닉네임/작성일자 등을 가져옴 <사이트마다 태그변경 또는 소스코드 수정 필요>
                commentInfor = {'userid': n['data-author-id'],
                                'userip' : n.find('span',{'class':'ip_address'}).text,
                                'username': name,
                                'datePublished': self.delrn(n.find('span',{'class':'timestamp'}).text).split('  / ')[0],
                                'Content': self.delrn(n.find('div',{'class':'comment_view'}).text),
                                'img' : [],
                                'reCmtCnt' : None,
                                'reComments' : []
                               }
                # 이미지가 있다면
                try:
                    commentInfor['img'].append(n.find('div',{'class':'comment-img'}).find('img')['src'])
                except:
                    None
                reCommentscounter = 0
                while True:
                    try:
                        if 're' in CommentList[cmtnum+1]['class']:
                            nn = CommentList[cmtnum+1]
                            name = self.delrn(nn.find('span',{'class':'nickname'}).text)
                            if name == "" : name = nn.find('span',{'class':'nickname'}).find('img')['alt']

                            # --- 댓글의 내용/작성자아이디/작성자닉네임/작성일자 등을 가져옴 <사이트마다 태그변경 또는 소스코드 수정 필요>
                            reComments = {'userid': nn['data-author-id'],
                                            'userip' : nn.find('span',{'class':'ip_address'}).text,
                                            'username': name,
                                            'datePublished': self.delrn(nn.find('span',{'class':'timestamp'}).text).split('  / ')[0],
                                            'Content': self.delrn(nn.find('div',{'class':'comment_view'}).text),
                                            'img' : []
                                            }
                            try:
                                reComments['img'].append(nn.find('div',{'class':'comment-img'}).find('img')['src'])
                            except:
                                None
                            commentInfor['reComments'].append(reComments)
                            cmtnum = cmtnum+1
                            replycounter = replycounter+1
                            reCommentscounter=reCommentscounter+1
                            if cmtnum+1 == len(CommentList):break
                        else:break
                    except:
                        break
                replycounter = replycounter+1
                commentInfor['reCmtCnt'] = reCommentscounter
                post['Comments'].append(commentInfor)
                if cmtnum+1 == len(CommentList):break
                cmtnum = cmtnum+1
            
            # ---

            # 해당 url 게시물 크롤링 완료
            post['CmtCnt'] = replycounter
            post['crawled'] = True
       

    def getCSV(self):
        today = datetime.now().now().strftime("%Y%m%d%H%M")
        pd.DataFrame(self.postUrls).to_csv("cwaling/"+today+self.keyword+"_"+self.site+".csv", encoding='utf-8-sig')
        print('[ * ] getCSV terminated')


if __name__=="__main__":   
    # 크롤러
    c = Crawler()

    # getList -> list (게시물 url 수집)
    c.getList()

    # getPost-> list (게시물 url로부터 게시물 상세정보 수집)
    c.getPost()

    # CSV로 출력
    c.getCSV()