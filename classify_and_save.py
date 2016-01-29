from sklearn.metrics import classification_report
from sklearn import cross_validation as cv
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV

def classify_and_save(clf, X, y, name, parameters, vect=None):
    
    X_train, X_test, y_train, y_test = cv.train_test_split(X,y)

    if vect == 'count':
        vectorizer = CountVectorizer(stop_words='english')
    elif vect == 'tfidf':
        vectorizer = TfidfVectorizer()
    elif vect== 'tfidf-bin':
        vectorizer = TfidfVectorizer(binary=True)
        
    pipeline = Pipeline([('vect',vectorizer),
                            ('clf', clf)])
    
    grid = GridSearchCV(pipeline, parameters)
    classifier = grid.fit(X_train, y_train)
   
    predictions = classifier.predict(X_test)
    report = classification_report(y_test, predictions)
    train_predictions = classifier.predict(X_train)
    train_report = classification_report(y_train, train_predictions)
    
    clf_score = classifier.score(X_test,y_test)
    clf_train_score = classifier.score(X_train, y_train)
 
    joblib.dump(classifier,name+'.pkl')
    joblib.dump(vectorizer,name+'_vect.pkl')
    joblib.dump(report, name+'_report.pkl')
    joblib.dump(clf_score, name+'_score.pkl')
    joblib.dump(train_report, name+'_train_report.pkl')
    joblib.dump(clf_train_score, name+'_train_score.pkl')
    
    print "Finished classifying {0}".format(name)
