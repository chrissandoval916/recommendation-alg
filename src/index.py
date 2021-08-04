import pandas as pd
from pandas.core.arrays.categorical import Categorical
from pandas.core.dtypes.dtypes import CategoricalDtype
import scipy.sparse as sparse
import numpy as np
from scipy.sparse.linalg import spsolve
import random
import implicit

retail_data = pd.read_excel("./data/OnlineRetail.xls") # This may take a couple minutes
cleaned_retail = retail_data.loc[pd.isnull(retail_data.CustomerID) == False]

cleaned_retail['CustomerID'] = cleaned_retail.CustomerID.astype(int)
cleaned_retail = cleaned_retail[['StockCode', 'Quantity', 'CustomerID']]
grouped_cleaned = cleaned_retail.groupby(['CustomerID', 'StockCode']).sum().reset_index()
grouped_cleaned.Quantity.loc[grouped_cleaned.Quantity == 0] = 1

grouped_purchased = grouped_cleaned.query('Quantity > 0')

customers = list(np.sort(grouped_purchased.CustomerID.unique()))
products = list(grouped_purchased.StockCode.unique())
quantity = list(grouped_purchased.Quantity)

rows_cat_type = CategoricalDtype(categories=customers, ordered=True)
rows = grouped_purchased.CustomerID.astype(rows_cat_type).cat.codes
cols_cat_type = CategoricalDtype(categories=products, ordered=True)
cols = grouped_purchased.StockCode.astype(cols_cat_type).cat.codes
purchases_sparse = sparse.csr_matrix((quantity, (rows, cols)), shape=(len(customers), len(products)))

matrix_size = purchases_sparse.shape[0]*purchases_sparse.shape[1]
num_purchases = len(purchases_sparse.nonzero()[0])
sparsity = 100*(1 - (num_purchases/matrix_size))

def make_train(ratings, pct_test = 0.2):
    '''
    This function will take in the original user-item matrix and "mask" a percentage of the original ratings where a
    user-item interaction has taken place for use as a test set. The test set will contain all of the original ratings, 
    while the training set replaces the specified percentage of them with a zero in the original ratings matrix. 
    
    parameters: 
    
    ratings - the original ratings matrix from which you want to generate a train/test set. Test is just a complete
    copy of the original set. This is in the form of a sparse csr_matrix. 
    
    pct_test - The percentage of user-item interactions where an interaction took place that you want to mask in the 
    training set for later comparison to the test set, which contains all of the original ratings. 
    
    returns:
    
    training_set - The altered version of the original data with a certain percentage of the user-item pairs 
    that originally had interaction set back to zero.
    
    test_set - A copy of the original ratings matrix, unaltered, so it can be used to see how the rank order 
    compares with the actual interactions.
    
    user_inds - From the randomly selected user-item indices, which user rows were altered in the training data.
    This will be necessary later when evaluating the performance via AUC.
    '''
    test_set = ratings.copy() # Make a copy of the original set to be the test set. 
    test_set[test_set != 0] = 1 # Store the test set as a binary preference matrix
    training_set = ratings.copy() # Make a copy of the original data we can alter as our training set. 
    nonzero_inds = training_set.nonzero() # Find the indices in the ratings data where an interaction exists
    nonzero_pairs = list(zip(nonzero_inds[0], nonzero_inds[1])) # Zip these pairs together of user,item index into list
    random.seed(0) # Set the random seed to zero for reproducibility
    num_samples = int(np.ceil(pct_test*len(nonzero_pairs))) # Round the number of samples needed to the nearest integer
    samples = random.sample(nonzero_pairs, num_samples) # Sample a random number of user-item pairs without replacement
    user_inds = [index[0] for index in samples] # Get the user row indices
    item_inds = [index[1] for index in samples] # Get the item column indices
    training_set[user_inds, item_inds] = 0 # Assign all of the randomly chosen user-item pairs to zero
    training_set.eliminate_zeros() # Get rid of zeros in sparse array storage after update to save space
    return training_set, test_set, list(set(user_inds)) # Output the unique list of user rows that were altered 



product_train, product_test, product_users_altered = make_train(purchases_sparse, pct_test = 0.2)

# initialize a model
model = implicit.als.AlternatingLeastSquares(factors=20, regularization = 0.1, iterations = 50)

# train the model on a sparse matrix of item/user/confidence weights
alpha = 15
model.fit((product_train*alpha).astype('double'))


# recommend items for a user
#user_items = item_user_data.T.tocsr()
#recommendations = model.recommend(userid, user_items)

# find related items
#related = model.similar_items(itemid)

#print(user_vecs[0,:].dot(item_vecs).toarray()[0,:5])