import math
import statistics
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.model_selection import KFold
from asl_utils import combine_sequences


class ModelSelector(object):
    '''
    base class for model selection (strategy design pattern)
    '''

    def __init__(self, all_word_sequences: dict, all_word_Xlengths: dict, this_word: str,
                 n_constant=3,
                 min_n_components=2, max_n_components=10,
                 random_state=14, verbose=False):
        self.words = all_word_sequences
        self.hwords = all_word_Xlengths
        self.sequences = all_word_sequences[this_word]
        self.X, self.lengths = all_word_Xlengths[this_word]
        self.this_word = this_word
        self.n_constant = n_constant
        self.min_n_components = min_n_components
        self.max_n_components = max_n_components
        self.random_state = random_state
        self.verbose = verbose
        self.all_word_Xlengths = all_word_Xlengths
    def select(self):
        raise NotImplementedError

    def base_model(self, num_states):
        # with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                    random_state=self.random_state, verbose=False).fit(self.X, self.lengths)
            if self.verbose:
                print("model created for {} with {} states".format(self.this_word, num_states))
            return hmm_model
        except:
            if self.verbose:
                print("failure on {} with {} states".format(self.this_word, num_states))
            return None


class SelectorConstant(ModelSelector):
    """ select the model with value self.n_constant

    """

    def select(self):
        """ select based on n_constant value

        :return: GaussianHMM object
        """
        best_num_components = self.n_constant
        return self.base_model(best_num_components)


class SelectorBIC(ModelSelector):
    """ select the model with the lowest Bayesian Information Criterion(BIC) score

    http://www2.imm.dtu.dk/courses/02433/doc/ch6_slides.pdf
    Bayesian information criteria: BIC = -2 * logL + p * logN
    """

    def select(self):
        """ select the best model for self.this_word based on
        BIC score for n between self.min_n_components and self.max_n_components

        :return: GaussianHMM object
        """
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)

        try:
            best_score = float("Inf")
            best_model = None
            for n_components in range(self.min_n_components, self.max_n_components + 1):

                hmm_model = self.base_model(n_components)
                logL = hmm_model.score(self.X, self.lengths)
                logN = np.log(len(self.X))
                parameters = n*n + 2*n*len(self.X[0]) - 1
                score = -2 * logL + parameters * logN

                if(score < best_score):
                	best_score = score
                	best_model = hmm_model
            return best_model
        except:
            return self.base_model(self.n_constant)



class SelectorDIC(ModelSelector):
    ''' select best model based on Discriminative Information Criterion

    Biem, Alain. "A model selection criterion for classification: Application to hmm topology optimization."
    Document Analysis and Recognition, 2003. Proceedings. Seventh International Conference on. IEEE, 2003.
    http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.58.6208&rep=rep1&type=pdf
    https://pdfs.semanticscholar.org/ed3d/7c4a5f607201f3848d4c02dd9ba17c791fc2.pdf
    DIC = log(P(X(i)) - 1/(M-1)SUM(log(P(X(all but i))
    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        try:
            best_score = float("-Inf")
            best_model = None
            list_of_words = self.words.keys()

            for n_components in range(self.min_n_components, self.max_n_components + 1):
                hmm_model = self.base_model(n_components)
                scores = []
                for word in list_of_words:
                    if (word != self.this_word):
                        word_X, word_lengths = self.all_word_Xlengths[word]
                        scores.append(hmm_model.score(word_X, word_lengths)) 
                score = hmm_model.score(self.X,self.lengths) - np.mean(scores)
                if (score > best_score):
                    best_score = score
                    best_model = hmm_model
            return best_model
        except:
            return self.base_model(self.n_constant)
       


class SelectorCV(ModelSelector):
    ''' select best model based on average log Likelihood of cross-validation folds

    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            best_score = float("-Inf")
            best_model = None

            for n_components in range(self.min_n_components, self.max_n_components + 1):
                split_method = KFold(n_splits=min(3,len(self.sequences)))
                logL_arr = []
                hmm_model = None
                for cv_train_idx, cv_test_idx in split_method.split(self.sequences):
                    self.X, self.lengths = combine_sequences(cv_train_idx, self.sequences)
                    hmm_model = self.base_model(n_components)

                    X_test, test_lengths = combine_sequences(cv_test_idx, self.sequences)
                    logL = hmm_model.score(X_test, test_lengths)

                    logL_arr.append(logL)

                avg_score = np.mean(logL_arr)

                if(avg_score > best_score):
                    best_score = avg_score
                    best_model = hmm_model
            return best_model
        except:
            return self.base_model(self.n_constant)
