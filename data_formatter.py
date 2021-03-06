import re
from nltk.tokenize import word_tokenize 
from databaseUpload import db_uploadFunction

class DataFormatter:
    def __init__(self, terms_file = "lists/final_keywords2.txt", 
                    languages = "lists/topLanguages.txt", 
                    industries = "lists/linkedin_industries.txt",
                    extra = "lists/extra_keywords.txt",
                    bug_file = "lists/bug_keywords.txt"):
        self.keywords = self.read_terms_file(terms_file)
        self.bug_words = self.read_terms_file(bug_file)
        self.extra_words = self.read_terms_file(extra)

        self.languages = self.read_terms_file(languages)
        self.linkedin_industries = open(industries,'r').read().split('\n')

        self.keywords = [item for item in self.keywords if item not in self.bug_words]
        self.keywords.extend(self.extra_words)
    def preprocessing(self,jobs_file):
        '''
        @Input pass in the file object, The file must contain 'BREAK<JOB ID>' between job posts
        @Output orig_posts (List of Strings) Each string is just original job post
        @Output job_posts (List of Strings) Each string is job post but with any that's not alphanumeric is replaced
        and all lower case. This means \n are replaced as blank spaces. 
        EXCEPTIONS: '+','#','-','_' is kept due to 'c++','c#','objective-c'
        @Output id_list (List of Int), a list of int, each int represents job ID in given order

        '''
        # jobsFile = open(jobs_file)
        jobs_lines = jobs_file.readlines()
        self.orig_posts = []
        self.job_posts = []
        self.id_list = []
        post = ""
        orig_post = ""
        first_one = True
        
        for l in range(len(jobs_lines)):
            if "BREAK" in jobs_lines[l]:
                self.id_list.append(int(jobs_lines[l][5:]))
                if first_one:
                    first_one = False
                else:
                    self.job_posts.append(post)
                    self.orig_posts.append(orig_post)
                    post = ""
                    orig_post = ""
                continue
            orig_post += jobs_lines[l]
            post+= re.sub(r'[^\w\s\+\#\-]', ' ', jobs_lines[l].lower())
            if l == len(jobs_lines)-1:
                self.job_posts.append(post)
                self.orig_posts.append(orig_post)
           # post += jobs_lines[l].replaceAll("[\\p{Punct}&&[^.]]", "").lower();
            

        print('----')
        for p in range(len(self.job_posts)):
            self.job_posts[p]= re.sub(' +', ' ', self.job_posts[p].replace('\n',' ')) #remove unnecessary double/triple white space
        # for p in range(len(job_posts)):
        #     job_posts[p] = word_tokenize(job_posts[p])
        # return orig_posts, job_posts, id_list

    
    def read_terms_file(self, terms_file_name):
        '''
        @Input the path of the file to be opened
        @Output return a list with each element a line in the file
        '''
        terms_file = open(terms_file_name,"r")
        terms = terms_file.readlines()
        print('opened:',terms_file_name)
        print('number terms:',len(terms))
        keywords = [term.rstrip('\n').lower() for term in terms]
        terms_file.close()
        return keywords

    #
    def extract_seniority(self, o_P):
        '''
        @Input list of strings o_P may contain a line "Seniority Level" (Linkedin Post attribute)
        @Output return the seniority level (standarlized) if there is one, the element (next line) after "Seniority Level" 
        '''
        seniority_levels = ['internship','entry level','associate','mid-senior level','director','executive']
        s_tag = ""
        s_boo =False
        #Some weird inconsistency with linkedin seniority level upperlower caseness, edge case
        if "Seniority Level" in o_P:
            s_tag = "Seniority Level"
            s_boo = True
        elif "Seniority level" in o_P:
            s_tag = "Seniority level"
            s_boo = True
        if s_boo:
            seniority_index = o_P.index(s_tag) +1 
            if o_P[seniority_index].lower() in seniority_levels:
                #print(o_P[seniority_index].lower())
                #print('SENIORITY:', seniority_levels[seniority_levels.index(o_P[seniority_index])])
                return o_P[seniority_index].lower()
            elif o_P[seniority_index] == "Not Applicable":
                return -1
            else:
                print("Doesn't exist in Linkedin's standard seniority levels, weird.")
                return -1
        else:
            return -1

    def extract_degree_lvl(self, post):
        deg_lvls = []
        deg_lvl = {
                   'a':['associate\'s','associate degree'],
                   'b':['ba','bs','bachelor','bachelor\'s','b s'],
                   'm':['master','ms','master\'s','m s'],
                   'p':['ph d','phd']

        }
        for d_key, d_value in deg_lvl.items():
            for variation in d_value:
                variation = " "+variation+" "
                if variation in post:
                    deg_lvls.append(d_key)
        #print('EDUCATION LEVEL',set(deg_lvls))
        return list(set(deg_lvls))
        
    def extract_degree_title(self, post):
        deg_titles = []
        deg_title = {'computer science':['computer science','cs','c s'],
                     'computer engineering':['computer engineering','ce','c e'],
                      'electrical engineering':['electrical engineering','ee','e e'],
                     'applied math':['applied math','applied mathematics'],
                     'physics':['physics'],
                     'statistics':['statistics'],
                     'bioinformatics/comp-bio':['bioinformatics','computational biology']

        }

        for d_key, d_value in deg_title.items():
            for title in d_value:
                title = " "+title+" "
                if title in post:
                    deg_titles.append(d_key)
           
       #print('DEGREE TITLE', set(deg_titles))
        return list(set(deg_titles))

    def extract_tech_terms(self, post,keywords):
        skills = []
        for key in keywords:
            key= " "+key+" "
            if key in post:
                skills.append(key.strip())
       #print('SKILLS',set(skills))
        return list(set(skills))

    def extract_languages(self, post,languages):
        '''
        @Input ASSUMES that the a language won't appear as the first or last word, the occurence of that happening
        is very not likely (these job posts always have starting/ending words), so didn't put in the case to handle
        otherwise
        '''
        lang = []
        for key in languages:
            key2= " "+key+" "
            if key2 in post:
                lang.append(key2.strip())
            elif (key in post) and (post.index(key) == 0 or post.index(key) == len(post)-len(key)):
                #the first word or last word
                lang.append(key)
       #print('SKILLS',set(skills))
        return list(set(lang))


    def extract_industry(self, o_P,linkedin_industries):

        s_tag = ""
        s_boo =False
        industries = []
        #Some weird inconsistency with inconsistency industry(ies) plural/singular, edge case
        if "Industry" in o_P:
            s_tag = "Industry"
            s_boo = True
        elif "Industries" in o_P:
            s_tag = "Industries"
            s_boo = True
        if s_boo:
            industry_index = o_P.index(s_tag) +1 
            for ind in linkedin_industries:
                if ind in o_P[industry_index] or ind.replace("&","and") in o_P[industry_index]:
                    industries.append(ind)
            #print('INDUSTRIES:', industries)
            return industries
        else:
            return []
    def extract_yoe(self, post):
        tokenize = post.split(' ')
        yoe_variation = ['years of experience',
        'years of full time','years full time',
        'years industry experience','years of industry experience',
        'years work experience','years of work experience']
        for w in range(len(tokenize)):
            if tokenize[w].isdigit():
                #print(tokenize[w-5:w],tokenize[w],tokenize[w+1:w+5])
                for yv in yoe_variation:
                    if yv in ' '.join(tokenize[w:w+6]):
                        #print('YOE:', tokenize[w])
                        return int(tokenize[w])
        #print('YOE:','N/A')
        return -1



    def data_extraction(self, job_name, do_upload):    
        '''
        @Input self.job_posts is a list of strings. Each job post is a long string with each word 
        lower cased. Punctuations are removed.
        '''      
        output = {}
        for i in range(len(self.job_posts)):  
            output[self.id_list[i]] = {}
            o_P = self.orig_posts[i].split('\n')
            #SENIORITY
            output[self.id_list[i]]['seniority']=self.extract_seniority(o_P)
            #INDUSTRY
            output[self.id_list[i]]['industry']=self.extract_industry(o_P,self.linkedin_industries)
            #Keyword Extraction -----
            #Languages
            output[self.id_list[i]]['languages'] = self.extract_languages(self.job_posts[i],self.languages)
            #TECH SKILLS
            output[self.id_list[i]]['skills']= self.extract_tech_terms(self.job_posts[i], self.keywords)
            #Degree level
            output[self.id_list[i]]['educationLevel'] = self.extract_degree_lvl(self.job_posts[i])
            #DEGREE TITLE
            output[self.id_list[i]]['degreeTitle'] = self.extract_degree_title(self.job_posts[i])
            #YoE
            output[self.id_list[i]]['yoe']= self.extract_yoe(self.job_posts[i])
            print()
            #Do the Data Base Upload and data validation, if specified
            if(do_upload):
                dbup_table = output[self.id_list[i]].copy()
                dbup_table['jobID'] = self.id_list[i]

                dbup_table['table'] = job_name.replace(" ", "")
                print(db_uploadFunction(dbup_table))
        return output
    


# orig_posts, job_posts, id_list = preprocessing("sample_job_posts.txt")
# print('There\'s',len(job_posts), 'job posts')
# keywords = read_terms_file("lists/final_keywords2.txt")
# languages = read_terms_file("lists/topLanguages.txt")
# linkedin_industries = open("lists/linkedin_industries.txt",'r').read().split('\n')
# print('opened lists/linkedin_industries.txt:\nnumber of terms',len(linkedin_industries))
# output = data_extraction(orig_posts, job_posts, keywords,id_list,linkedin_industries,languages)
# import pprint

#pprint.pprint(output)
