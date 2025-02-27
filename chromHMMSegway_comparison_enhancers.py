# how much do they overlap (union intersect) for all the labels.
# how much do they overlap with the detected enhancers for the cell type - each.
# distribution of enhancer labels for the two samples. Samples investigated separately. (I can change the model if I like it)

# TODO: get the average genome coverage for whatever samples we are comparing

########################################
# Phantom5 enhancer analyses is pending until I find stuff
########################################

import linecache
import pickle
import re
import numpy as np
import pandas as pd
import subprocess as sp
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from QC_transcriptionComparison_util import Gene, Exon, Annotation, AnnotationClass

import glob

# General data folder
dataFolder = '/Users/marjanfarahbod/Documents/projects/segwayLabeling/data/'

dataSubFolder = 'testBatch105/fromAPI/'

# GTF data structure
fileName = dataFolder + '/geneLists.pkl'
with open(fileName, 'rb') as pickleFile:
    geneListsAndIDs = pickle.load(pickleFile)
    
geneList = geneListsAndIDs[0]
geneIDList = geneListsAndIDs[1]
del geneListsAndIDs

inputFile = dataFolder + dataSubFolder + 'metaInfo.pkl'
with open(inputFile, 'rb') as f:
    annMeta = pickle.load(f)

annAccessionList = list(annMeta.keys())

inputFile = dataFolder + dataSubFolder + 'chmmFile_list_dict.pkl'
with open(inputFile, 'rb') as f:
    chmmFile_dict = pickle.load(f)

book =  'EnhA1 EnhA2 EnhBiv EnhG1 EnhG2 EnhWk Het Quies ReprPC ReprPCWk TssA TssBiv TssFlnk TssFlnkD TssFlnkU Tx TxWk ZNF/Rpts'
chromLabels = book.split()

# chrom and segway coverage distribution
########################################

segwayLabels = ['Enhancer', 'EnhancerLow', 'Promoter', 'PromoterFlanking', 'Transcribed', 'CTCF', 'K9K36', 'Bivalent', 'FacultativeHet', 'ConstitutiveHet', 'Quiescent']

chromLabels_reordered = ['EnhA1', 'EnhA2', 'EnhBiv', 'EnhG1', 'EnhG2', 'EnhWk', 'TssA',  'TssFlnk', 'TssFlnkD', 'TssFlnkU', 'Tx', 'TxWk', 'ReprPC', 'ReprPCWk', 'ZNF/Rpts', 'TssBiv','Het', 'Quies' ]

chromLabels_merged  = ['Enh', 'EnhWk', 'Tss', 'TssFlnk', 'Tx', 'ReprPC', 'ReprPCWk', 'ZNF/Rpts', 'TssBiv', 'Het', 'Quies']

chromCoverage = np.zeros((len(annAccessionList), 18))
segwayCoverage = np.zeros((len(annAccessionList), len(segwayLabels)))
sampleCount = 0
for annAccession in annAccessionList:

    sampleFolderAdd = dataFolder + dataSubFolder + annAccession + '/'
    # get the name of the segway bed file from annMeta
    originalBedFile = annMeta[annAccession]['bedFile']
    bedAccession = originalBedFile.split('.')[0]

    chmmFile = chmmFile_dict[annAccession]
    if chmmFile == 'none':
        continue

    chmmAccession = re.search('ENCFF.*\.', chmmFile)[0][:-1]
    
    inputFileName = 'overlap_segway_%s_chmm_%s.pkl' %(bedAccession, chmmAccession)
    inputFile = dataFolder + dataSubFolder + annAccession + '/' + inputFileName
    with open(inputFile, 'rb') as f:
        overlap = pickle.load(f)

    overlap_mat = overlap.to_numpy()
    # get the axis labels
    segway_cluster_list_old = list(overlap.index.values)
    chmm_class_list = list(overlap.columns.values)

    # load the updated mnemonics
    label_term_mapping = {}
    mnemonics_file = sampleFolderAdd + 'mnemonics_v04.txt'
    with open(mnemonics_file, 'r') as mnemonics:
        for line in mnemonics:
            #print(line)
            label = line.strip().split()[0]
            term = line.strip().split()[1]
            label_term_mapping[label] = term

    # change segway_cluster_list_updated based on the mnemonics
    segway_cluster_list = []
    for cluster in segway_cluster_list_old:
        label = cluster.split('_')[0]
        term = label_term_mapping[label]
        segway_cluster_list.append(label + '_' + term)


    # total bp count that is covered by both annotations
    total_bp = np.sum(overlap_mat)

    # fraction of base pairs in each label to the total bp count
    chmm_labelFraction = np.sum(overlap_mat, axis = 0) / total_bp
    segway_labelFraction = np.sum(overlap_mat, axis = 1) / total_bp

    # TODO: do the loop for the segway coverage
    segFracList = np.zeros(len(segwayLabels))
    for i,label in enumerate(segwayLabels):
        for j, sampleLabel in enumerate(segway_cluster_list):
            if sampleLabel.split('_')[1] == label:
                segFracList[i] += segway_labelFraction[j]

    chromFracList = np.zeros(len(chromLabels))
    for i, label in enumerate(chromLabels_reordered):
        for j,sampleLabel in enumerate(chromLabels):
            if sampleLabel == label:
                chromFracList[i] = chmm_labelFraction[j]

    chromCoverage[sampleCount, :] = chromFracList
    segwayCoverage[sampleCount, :] = segFracList
    sampleCount +=1

segwayCoverage = segwayCoverage[0:sampleCount,:]
chromCoverage = chromCoverage[0:sampleCount, :]

# fixing the mergedchrom
chromCoverage_merged = np.zeros((sampleCount, len(chromLabels_merged)))
chromCoverage_merged[:, 0] = np.sum(chromCoverage[:, 0:5], axis=1) # enh
chromCoverage_merged[:, 1] = chromCoverage[:, 5] # enhLow
chromCoverage_merged[:, 2] = chromCoverage[:, 6] # promoter
chromCoverage_merged[:, 3] = np.sum(chromCoverage[:, 7:10], axis=1) # promoterFlank
chromCoverage_merged[:, 4] = np.sum(chromCoverage[:, 10:12], axis=1) # transcribed
chromCoverage_merged[:, 5] = chromCoverage[:, 12] # that thing
chromCoverage_merged[:, 6] = chromCoverage[:, 13] # that other thing
chromCoverage_merged[:, 7] = chromCoverage[:, 14] # znf
chromCoverage_merged[:, 8] = chromCoverage[:, 15] # biv
chromCoverage_merged[:, 9] = chromCoverage[:, 16] # het
chromCoverage_merged[:, 10] = chromCoverage[:, 17] # Quis

plt.boxplot(segwayCoverage)
plt.ylim((-.1,.85))
plt.show()

fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(9, 4))

# rectangular box plot
bplot1 = axs[0].boxplot(segwayCoverage,
                    vert=True,  # vertical box alignment
                    patch_artist=True,
                    showfliers=False)  # color
axs[0].set_title('Rectangular box plot')
axs[0].set_ylim((-.1, 1))

# notch shape box plot
bplot2 = axs[1].boxplot(chromCoverage_merged,
                    vert=True,  # vertical box alignment
                    patch_artist=True,
                    showfliers=False)  # fill with color
axs[1].set_title('Rectangular box plot')
axs[1].set_ylim((-.1, 1))

#plt.show()
# fill with colors
colors = ['pink', 'lightblue']
color = 'gray'
for bplot in (bplot1, bplot2):
    for patch in bplot['boxes']:
        patch.set_facecolor(color)
            
plt.show()

# adding horizontal grid lines
for ax in [ax1, ax2]:
    ax.yaxis.grid(True)
    ax.set_xlabel('Three separate samples')
    ax.set_ylabel('Observed values')

plt.show()

fix, axs = plt.subplots(nrow1,2, )
plt.boxplot(chromCoverage_merged)
plt.show()

plt.boxplot(chromCoverage)
plt.ylim((0,.85))
plt.show()


# chromhmm segway comparison
########################################

segwayLabels = ['EnhancerLow', 'Enhancer', 'PromoterFlanking', 'Promoter', 'Transcribed', 'CTCF', 'K9K36', 'Bivalent', 'FacultativeHet', 'ConstitutiveHet', 'Quiescent']

for annAccession in annAccessionList:

    sampleFolderAdd = dataFolder + dataSubFolder + annAccession + '/'
    # get the name of the segway bed file from annMeta
    originalBedFile = annMeta[annAccession]['bedFile']
    bedAccession = originalBedFile.split('.')[0]

    chmmFile = chmmFile_dict[annAccession]
    chmmAccession = re.search('ENCFF.*\.', chmmFile)[0][:-1]
    
    inputFileName = 'overlap_segway_%s_chmm_%s.pkl' %(bedAccession, chmmAccession)
    inputFile = dataFolder + dataSubFolder + annAccession + '/' + inputFileName
    with open(inputFile, 'rb') as f:
        overlap = pickle.load(f)

    overlap_mat = overlap.to_numpy()

    # total bp count that is covered by both annotations
    total_bp = np.sum(overlap_mat)

    # fraction of base pairs in each label to the total bp count
    chmm_labelFraction = np.sum(overlap_mat, axis = 0) / total_bp
    segway_labelFraction = np.sum(overlap_mat, axis = 1) / total_bp

    # get the observed versus the expected fraction
    expectedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            expectedFraction_mat[i][j] = segway_labelFraction[i] * chmm_labelFraction[j]

    observedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            observedFraction_mat[i][j] = overlap_mat[i][j] / total_bp

    obs_exp = np.divide(observedFraction_mat, expectedFraction_mat)

    # get the normalized value
    overlap_mat_colNorm = overlap_mat / np.sum(overlap_mat, axis=0)[np.newaxis, :] # chmm
    overlap_mat_rowNorm = overlap_mat / np.sum(overlap_mat, axis=1)[:, np.newaxis] # segway

    # get the axis labels
    segway_cluster_list_old = list(overlap.index.values)
    chmm_class_list = list(overlap.columns.values)
    
    # load the updated mnemonics
    label_term_mapping = {}
    mnemonics_file = sampleFolderAdd + 'mnemonics_v04.txt'
    with open(mnemonics_file, 'r') as mnemonics:
        for line in mnemonics:
            #print(line)
            label = line.strip().split()[0]
            term = line.strip().split()[1]
            label_term_mapping[label] = term

    # change segway_cluster_list_updated based on the mnemonics
    segway_cluster_list = []
    for cluster in segway_cluster_list_old:
        label = cluster.split('_')[0]
        term = label_term_mapping[label]
        segway_cluster_list.append(label + '_' + term)

    # reorder the cluster list
    segway_cluster_list_reordered = []
    for label in segwayLabels:
        for cluster in segway_cluster_list:
            if cluster.split('_')[1] == label:
                segway_cluster_list_reordered.append(cluster)

    # add the ratio to the axis labels
    segwayAxis_list = []
    for i, cluster in enumerate(segway_cluster_list):
        segwayAxis_list.append(cluster + '_' + str(round(segway_labelFraction[i], 4)))

    segwayAxis_list_reordered = []
    for label in segwayLabels:
        for axis in segwayAxis_list:
            if axis.split('_')[1] == label:
                segwayAxis_list_reordered.append(axis)

    chmm_class_list = list(overlap.columns.values)

    chmmAxis_list = []
    for i, chmmclass in enumerate(chmm_class_list):
        chmmAxis_list.append(chmmclass + '_' + str(round(chmm_labelFraction[i], 4)))

    fig, axs = plt.subplots(1, 3, figsize=(16,4.2))
    
    obs_exp_log = np.log10(obs_exp, out=np.zeros_like(obs_exp), where=(obs_exp!=0))
    obs_exp_log = np.where(obs_exp_log < 0, 0, obs_exp_log)

    h1 = pd.DataFrame(obs_exp_log, index = segwayAxis_list, columns = chmmAxis_list)
    h1 = h1.reindex(segwayAxis_list_reordered)
    #cmap = sns.diverging_palette(240, 10, s=100, l=30, as_cmap=True)
    cmap = sns.diverging_palette(240, 10, s=80, l=30, as_cmap=True)
    g1 = sns.heatmap(h1, center = 0,cmap=cmap, ax=axs[0])
    #g1.set_ylabel('this')
    #g1.set_xlabel('that')
    g1.set_title('ratio - log (observed to expected)')
    #g1.set_xticklabels(g1.get_xticklabels(), rotation=45)
    #plt.ylabel('segway')
    #plt.ylabel('chmm')
    #plt.subplots_adjust(left=.075, right=.95, top=.9, bottom=.25)
    sns.set(font_scale=.8)
    plt.tight_layout()
    #plt.title('ratio - observed vs expected')
    #plt.show()


    h1 = pd.DataFrame(overlap_mat_colNorm, index = segwayAxis_list, columns = chmmAxis_list)
    h1 = h1.reindex(segwayAxis_list_reordered)
    cmap = sns.diverging_palette(240, 10, s=80, l=30, as_cmap=True)
    g1 = sns.heatmap(h1, center = 0,cmap=cmap, ax=axs[1])
    #g1.set_ylabel('this')
    #g1.set_xlabel('that')
    g1.set_title('ratio of bp overlap - chmm')
    #plt.ylabel('segway')
    #plt.ylabel('chmm')
    #plt.subplots_adjust(left=.075, right=.95, top=.9, bottom=.25)
    plt.tight_layout()
    
    h2 = pd.DataFrame(overlap_mat_rowNorm, index = segwayAxis_list, columns = chmmAxis_list)
    h2 = h2.reindex(segwayAxis_list_reordered)
    cmap = sns.diverging_palette(240, 10, s=80, l=30, as_cmap=True)
    g2 = sns.heatmap(h2, center = 0,cmap=cmap, ax=axs[2])
    #g1.set_ylabel('this')
    #g1.set_xlabel('that')
    g2.set_title('ratio of bp overlap - Segway')
    #plt.ylabel('segway')
    #plt.ylabel('chmm')
    #plt.subplots_adjust(left=.075, right=.95, top=.9, bottom=.25)
    plt.tight_layout()

    plt.show()

# I am looking for a measurement between the samples that I can compare
# which percentage of the enhancer labels are covered with log10 = 1 overlap
# it is important to note that Segway identifies far more bs as enhancers as chromhmm
########################################

# what fraction of base-pairs from chmm enhancer regions were covered by Segway Enhacer/enhancerLow with more than log ratio .3

segwayLabels = ['Enhancer', 'EnhancerLow', 'Promoter', 'PromoterFlanking', 'Transcribed', 'CTCF', 'K9K36', 'Bivalent', 'FacultativeHet', 'ConstitutiveHet', 'Quiescent']

# ITSELF
# bestmatch
bestMatch = {}
bestMatchValue = {}
for annAccession in annAccessionList[0:10]:

    print(annAccession)

    sampleFolderAdd = dataFolder + dataSubFolder + annAccession + '/'
    # get the name of the segway bed file from annMeta
    originalBedFile = annMeta[annAccession]['bedFile']
    bedAccession = originalBedFile.split('.')[0]

    chmmFile = chmmFile_dict[annAccession]
    if chmmFile == 'none':
        continue
    chmmAccession = re.search('ENCFF.*\.', chmmFile)[0][:-1]
    inputFileName = 'overlap_segway_%s_chmm_%s.pkl' %(bedAccession, chmmAccession)
    inputFile = dataFolder + dataSubFolder + annAccession + '/' + inputFileName
    with open(inputFile, 'rb') as f:
        overlap = pickle.load(f)

    overlap_mat = overlap.to_numpy()

    # total bp count that is covered by both annotations
    total_bp = np.sum(overlap_mat)

    # fraction of base pairs in each label to the total bp count
    chmm_labelFraction = np.sum(overlap_mat, axis = 0) / total_bp
    segway_labelFraction = np.sum(overlap_mat, axis = 1) / total_bp

    # get the observed versus the expected fraction
    expectedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            expectedFraction_mat[i][j] = segway_labelFraction[i] * chmm_labelFraction[j]

    observedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            observedFraction_mat[i][j] = overlap_mat[i][j] / total_bp

    obs_exp = np.divide(observedFraction_mat, expectedFraction_mat)

    # get the normalized value
    overlap_mat_colNorm = overlap_mat / np.sum(overlap_mat, axis=0)[np.newaxis, :] # chmm
    overlap_mat_rowNorm = overlap_mat / np.sum(overlap_mat, axis=1)[:, np.newaxis] # segway

    segway_cluster_list_old = list(overlap.index.values)
    
    # load the updated mnemonics
    label_term_mapping = {}
    mnemonics_file = sampleFolderAdd + 'mnemonics_v04.txt'
    with open(mnemonics_file, 'r') as mnemonics:
        for line in mnemonics:
            #print(line)
            label = line.strip().split()[0]
            term = line.strip().split()[1]
            label_term_mapping[label] = term

    # change segway_cluster_list_updated based on the mnemonics
    segway_cluster_list = []
    for cluster in segway_cluster_list_old:
        label = cluster.split('_')[0]
        term = label_term_mapping[label]
        segway_cluster_list.append(label + '_' + term)

    # reorder the cluster list
    segway_cluster_list_reordered = []
    for label in segwayLabels:
        for cluster in segway_cluster_list:
            if cluster.split('_')[1] == label:
                segway_cluster_list_reordered.append(cluster)

    # add the ratio to the axis labels
    segwayAxis_list = []
    segEnh_inds = []
    for i, cluster in enumerate(segway_cluster_list):
        segwayAxis_list.append(cluster + '_' + str(round(segway_labelFraction[i], 4)))
        if cluster.split('_')[1] == 'Enhancer':
            segEnh_inds.append(i)

    segwayAxis_list_reordered = []
    for label in segwayLabels:
        for axis in segwayAxis_list:
            if axis.split('_')[1] == label:
                segwayAxis_list_reordered.append(axis)

    chmm_class_list = list(overlap.columns.values)

    chmmAxis_list = []
    for i, chmmclass in enumerate(chmm_class_list):
        chmmAxis_list.append(chmmclass + '_' + str(round(chmm_labelFraction[i], 4)))

    obs_exp_log = np.log10(obs_exp, out=np.zeros_like(obs_exp), where=(obs_exp!=0))
    obs_exp_log = np.where(obs_exp_log < 0, 0, obs_exp_log)

    sumCovVal = np.zeros(len(segwayAxis_list))
    for i in range(len(segwayAxis_list)):
        sumCovVal[i] = np.sum(overlap_mat_colNorm[i,0:6]* obs_exp_log[i, 0:6])

    book = np.argsort(sumCovVal)
    for i in book:
        print('%s  %.4f' %(segwayAxis_list[i], sumCovVal[i]))

    bestMatch[annAccession] = segwayAxis_list[book[-1]]
    bestMatchValue[annAccession] = sumCovVal[book[-1]]
    
    # find the rows with label Enhancer (just that)
    # get the coverage ratio from the cells with log > .3

# OTHERS
########################################


segwayLabels = ['Enhancer', 'EnhancerLow', 'Promoter', 'PromoterFlanking', 'Transcribed', 'CTCF', 'K9K36', 'Bivalent', 'FacultativeHet', 'ConstitutiveHet', 'Quiescent']

allMatch = {}
#selfMatch = {}
#selfMatchValue = {}
selfMatch = {}
for annAccession in annAccessionList[0:30]:

    print(annAccession)

    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

    sampleFolderAdd = dataFolder + dataSubFolder + annAccession + '/'
    # get the name of the segway bed file from annMeta
    originalBedFile = annMeta[annAccession]['bedFile']
    bedAccession = originalBedFile.split('.')[0]

    chmmFile = chmmFile_dict[annAccession]
    if chmmFile == 'none':
        continue
    chmmAccession = re.search('ENCFF.*\.', chmmFile)[0][:-1]
    
    inputFileName = 'overlap_segway_%s_chmm_%s.pkl' %(bedAccession, chmmAccession)
    inputFile = dataFolder + dataSubFolder + annAccession + '/' + inputFileName
    with open(inputFile, 'rb') as f:
        overlap = pickle.load(f)

    # do it for the self file
    overlap_mat = overlap.to_numpy()

    print(inputFileName)

    # total bp count that is covered by both annotations
    total_bp = np.sum(overlap_mat)

    # fraction of base pairs in each label to the total bp count
    chmm_labelFraction = np.sum(overlap_mat, axis = 0) / total_bp
    segway_labelFraction = np.sum(overlap_mat, axis = 1) / total_bp

    # get the observed versus the expected fraction
    expectedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            expectedFraction_mat[i][j] = segway_labelFraction[i] * chmm_labelFraction[j]

    observedFraction_mat = np.zeros(overlap_mat.shape)
    for i in range(len(segway_labelFraction)):
        for j in range(len(chmm_labelFraction)):
            observedFraction_mat[i][j] = overlap_mat[i][j] / total_bp

    obs_exp = np.divide(observedFraction_mat, expectedFraction_mat)
    
    # get the normalized value
    overlap_mat_colNorm = overlap_mat / np.sum(overlap_mat, axis=0)[np.newaxis, :] # chmm
    overlap_mat_rowNorm = overlap_mat / np.sum(overlap_mat, axis=1)[:, np.newaxis] # segway

    segway_cluster_list_old = list(overlap.index.values)
    
    # load the updated mnemonics
    label_term_mapping = {}
    mnemonics_file = sampleFolderAdd + 'mnemonics_v04.txt'
    with open(mnemonics_file, 'r') as mnemonics:
        for line in mnemonics:
            #print(line)
            label = line.strip().split()[0]
            term = line.strip().split()[1]
            label_term_mapping[label] = term

    # change segway_cluster_list_updated based on the mnemonics
    segway_cluster_list = []
    for cluster in segway_cluster_list_old:
        label = cluster.split('_')[0]
        term = label_term_mapping[label]
        segway_cluster_list.append(label + '_' + term)

    # reorder the cluster list
    segway_cluster_list_reordered = []
    for label in segwayLabels:
        for cluster in segway_cluster_list:
            if cluster.split('_')[1] == label:
                segway_cluster_list_reordered.append(cluster)

    # add the ratio to the axis labels
    segwayAxis_list = []
    segEnh_inds = []
    for i, cluster in enumerate(segway_cluster_list):
        segwayAxis_list.append(cluster + '_' + str(round(segway_labelFraction[i], 4)))
        if cluster.split('_')[1] == 'Enhancer':
            segEnh_inds.append(i)

    segwayAxis_list_reordered = []
    for label in segwayLabels:
        for axis in segwayAxis_list:
            if axis.split('_')[1] == label:
                segwayAxis_list_reordered.append(axis)

    chmm_class_list = list(overlap.columns.values)

    chmmAxis_list = []
    for i, chmmclass in enumerate(chmm_class_list):
        chmmAxis_list.append(chmmclass + '_' + str(round(chmm_labelFraction[i], 4)))

    obs_exp_log = np.log10(obs_exp, out=np.zeros_like(obs_exp), where=(obs_exp!=0))
    obs_exp_log = np.where(obs_exp_log < 0, 0, obs_exp_log)
    
    totEnhancerPerChromLabel = np.sum(overlap_mat[:, [0,1,3,4]], 1) # total enhancer bps for different chrom enhancers
    totalEnhancer = sum(totEnhancerPerChromLabel)
    # chromEnhFracsSelf = totEnhancer /(sum(totEnhancer)) # the fraction of total enhancer labels

    enhOverlap_enhNorm = overlap_mat[:, [0,1,3,4]]/totalEnhancer # ratio of chrom enhancer labels for labels of segway (notice that it is normalized by the total enhancer labels, this will read: cell i,j has the r amount of total chrom enhancer labels labeld with segway i label and chrom j label)
    chromEnhFracsSelf = np.sum(enhOverlap_enhNorm, axis = 1)
    
    #chromEnhFracsSelf = np.sum(overlap_mat_colNorm[:, 0:6], axis =1)

    #  getting the (overlap-ratio * logoe-ratio) of the chrom enhancers, for each segway labels
    # the meanLog has the average of the above value for the coverage of the ChromEnhancer label
    obs_exp_log_enh = obs_exp_log[:, [0,1,3,4]]
    sumCovVal = np.zeros(len(segwayAxis_list))
    meanLog = np.zeros(len(segwayAxis_list))
    for i in range(len(segwayAxis_list)):
        #sumCovVal[i] = np.sum(overlap_mat_colNorm[i,0:6]* obs_exp_log[i, 0:6]) # ***
        sumCovVal[i] = np.sum(enhOverlap_enhNorm[i,:]* obs_exp_log_enh[i,:])
        #meanLog[i] = np.mean(obs_exp_log[i, 0:6])
        meanLog[i] = sumCovVal[i] / chromEnhFracsSelf[i]

    selfMatch[annAccession] = (segwayAxis_list, sumCovVal, chromEnhFracsSelf, meanLog)

    #book = np.argsort(sumCovVal)
    #for i in book:
        #print('%s  %.4f' %(segwayAxis_list[i], sumCovVal[i]))

    #selfMatch[annAccession] = segwayAxis_list[book[-1]]
    #selfMatchValue[annAccession] = sumCovVal[book[-1]]

    #bestMatch = {}
    #bestMatchVal = {}
    matchList = {}
    matchVal = {}
    chromEnhFracs = {}
    meanLogs = {}
    for nonSelfAccession in annAccessionList:

        if nonSelfAccession == annAccession:
            continue

        if nonSelfAccession == 'ENCSR313QGL' or nonSelfAccession == 'ENCSR592IOP' or nonSelfAccession == 'ENCSR721USS' or nonSelfAccession == 'ENCSR273LUT' or nonSelfAccession == 'ENCSR699DMW':
            continue
        
        chmmFile = chmmFile_dict[nonSelfAccession]

        if chmmFile == 'none':
            continue

        print('here')

        chmmAccession = re.search('ENCFF.*\.', chmmFile)[0][:-1]
    
        inputFileName = 'overlap_segway_%s_chmm_%s_nonself.pkl' %(bedAccession, chmmAccession)
        inputFile = dataFolder + dataSubFolder + annAccession + '/' + inputFileName
        with open(inputFile, 'rb') as f:
            overlap = pickle.load(f)

        overlap_mat = overlap.to_numpy()

        print(inputFileName)

        # total bp count that is covered by both annotations
        total_bp = np.sum(overlap_mat)

        # fraction of base pairs in each label to the total bp count
        chmm_labelFraction = np.sum(overlap_mat, axis = 0) / total_bp
        segway_labelFraction = np.sum(overlap_mat, axis = 1) / total_bp

        # get the observed versus the expected fraction
        expectedFraction_mat = np.zeros(overlap_mat.shape)
        for i in range(len(segway_labelFraction)):
            for j in range(len(chmm_labelFraction)):
                expectedFraction_mat[i][j] = segway_labelFraction[i] * chmm_labelFraction[j]

        observedFraction_mat = np.zeros(overlap_mat.shape)
        for i in range(len(segway_labelFraction)):
            for j in range(len(chmm_labelFraction)):
                observedFraction_mat[i][j] = overlap_mat[i][j] / total_bp

        obs_exp = np.divide(observedFraction_mat, expectedFraction_mat)

        # get the normalized value
        overlap_mat_colNorm = overlap_mat / np.sum(overlap_mat, axis=0)[np.newaxis, :] # chmm
        overlap_mat_rowNorm = overlap_mat / np.sum(overlap_mat, axis=1)[:, np.newaxis] # segway

        segway_cluster_list_old = list(overlap.index.values)
    
        # load the updated mnemonics
        label_term_mapping = {}
        mnemonics_file = sampleFolderAdd + 'mnemonics_v04.txt'
        with open(mnemonics_file, 'r') as mnemonics:
            for line in mnemonics:
                #print(line)
                label = line.strip().split()[0]
                term = line.strip().split()[1]
                label_term_mapping[label] = term

        # change segway_cluster_list_updated based on the mnemonics
        segway_cluster_list = []
        for cluster in segway_cluster_list_old:
            label = cluster.split('_')[0]
            term = label_term_mapping[label]
            segway_cluster_list.append(label + '_' + term)

        # reorder the cluster list
        segway_cluster_list_reordered = []
        for label in segwayLabels:
            for cluster in segway_cluster_list:
                if cluster.split('_')[1] == label:
                    segway_cluster_list_reordered.append(cluster)

        # add the ratio to the axis labels
        segwayAxis_list = []
        segEnh_inds = []
        for i, cluster in enumerate(segway_cluster_list):
            segwayAxis_list.append(cluster + '_' + str(round(segway_labelFraction[i], 4)))
            if cluster.split('_')[1] == 'Enhancer':
                segEnh_inds.append(i)

        segwayAxis_list_reordered = []
        for label in segwayLabels:
            for axis in segwayAxis_list:
                if axis.split('_')[1] == label:
                    segwayAxis_list_reordered.append(axis)

        chmm_class_list = list(overlap.columns.values)

        chmmAxis_list = []
        for i, chmmclass in enumerate(chmm_class_list):
            chmmAxis_list.append(chmmclass + '_' + str(round(chmm_labelFraction[i], 4)))

        obs_exp_log = np.log10(obs_exp, out=np.zeros_like(obs_exp), where=(obs_exp!=0))
        obs_exp_log = np.where(obs_exp_log < 0, 0, obs_exp_log)

        totEnhancerPerChromLabel = np.sum(overlap_mat[:,[0,1,3,4]], 1) # total enhancer bps for different chrom enhancers
        totalEnhancer = sum(totEnhancerPerChromLabel)
        # chromEnhFracsSelf = totEnhancer /(sum(totEnhancer)) # the fraction of total enhancer labels

        enhOverlap_enhNorm = overlap_mat[:, [0,1,3,4]]/totalEnhancer # ratio of chrom enhancer labels for labels of segway (notice that it is normalized by the total enhancer labels, this will read: cell i,j has the r amount of total chrom enhancer labels labeld with segway i label and chrom j label)
        chromEnhFrac = np.sum(enhOverlap_enhNorm, axis = 1)
    
        #totEnhancer = np.sum(overlap_mat[:,0:6], 1) # total bps for chrom enhancers # ***
        #chromEnhFrac = totEnhancer /(sum(totEnhancer)) # ratio of bs for chrom enhancers #***

        sumCovVal = np.zeros(len(segwayAxis_list))
        meanLog = np.zeros(len(segwayAxis_list))
        for i in range(len(segwayAxis_list)):
            #sumCovVal[i] = np.sum(overlap_mat_colNorm[i,0:6]* obs_exp_log[i, 0:6]) #***
            sumCovVal[i] = np.sum(enhOverlap_enhNorm[i,:]* obs_exp_log[i, [0,1,3,4]])
            #meanLog[i] = np.mean(obs_exp_log[i, 0:6])
            meanLog[i] = sumCovVal[i] / chromEnhFrac[i]

        #book = np.argsort(sumCovVal)
        #for i in book:
            #print('%s  %.4f' %(segwayAxis_list[i], sumCovVal[i]))


        #bestMatch[nonSelfAccession] = segwayAxis_list[book[-1]]
        #bestMatchVal[nonSelfAccession] = sumCovVal[book[-1]]

        #matchList[nonSelfAccession] = segwayAxis_list
        matchVal[nonSelfAccession] = sumCovVal
        chromEnhFracs[nonSelfAccession] = chromEnhFrac
        meanLogs[nonSelfAccession] = meanLog

    #allMatch[annAccession] = (bestMatch, bestMatchVal)
    allMatch[annAccession] = (segwayAxis_list, matchVal, chromEnhFracs, meanLogs)

        # find the rows with label Enhancer (just that)
    # get the coverage ratio from the cells with log > .3

### sumCovVal divided by fracs will give me the mean logs

##### now parsing it all
########################################

allMatch 
selfMatch

labelColor = np.zeros((31,105))
labelCoverage = np.zeros((31,105))
labelCluster = np.zeros((31,105))
labelCovOther = np.zeros((31,105))
labelGenomeCover = np.zeros((31,105))
overlapLog = np.zeros((31,105))

selfCov = {} # for each Segway, it's own chromhmm
allCov = {} # for each segway, all the chroms
# TODO: skip the label with < .3 obs/exp

for  s, annAccession in enumerate(annAccessionList[0:30]):

    if not(annAccession in list(selfMatch.keys())):
        continue

    #print('****************************************')
    #print('****************************************')
    selfMatchThis = selfMatch[annAccession]
    #print(annAccession)
    #print(s)

    # getting the top index for the self overlap
    sumCovVal = selfMatchThis[1]  # this can be normalized
    book = np.argsort(sumCovVal)[::-1]

    topIndsSelf = book[0:3]

    fracs = selfMatchThis[2]
    #print('SELF: coverage with the top 3 labels')
    #print(sum(fracs[topIndsSelf]))
    #print('SELF: coverage with the first lael')
    #print(fracs[topIndsSelf[0]])
    #print('-------')

    # the mean log ratio overlap
    #print('SELF: the mean Log OBS/EXP overlap - 4 chrom labels')
    #print(selfMatchThis[3][topIndsSelf])

    #print(sum(sumCovVal[topIndsSelf])*sum(fracs[topIndsSelf]))

    selfCov[annAccession] = sum(fracs[topIndsSelf])

    #print('top 3 labels')
    labels = selfMatchThis[0]
    #for ind in topIndsSelf:
    #   print(labels[ind])

    thisLabel = labels[topIndsSelf[0]]
    thisTerm = thisLabel.split('_')[1]
    termIndSelf = segwayLabels.index(thisTerm)

    labelColor[s,s] = termIndSelf
    labelCoverage[s,s] = fracs[topIndsSelf[0]]
    labelCluster[s,s] = thisLabel.split('_')[0]
    labelCovOther[s,s] = fracs[topIndsSelf[0]]
    labelGenomeCover[s,s] = float(thisLabel.split('_')[2])
    overlapLog[s,s] = selfMatchThis[3][topIndsSelf[0]]

    print('-----')
    print(s)
    print(thisLabel)
    print(thisLabel.split('_')[0])
    print(termIndSelf)
    print('--')

    allMatchThis = allMatch[annAccession]

    nonKeys = list(allMatchThis[1].keys())
 
    segLabels = allMatchThis[0]

    otherCov = {}
    # for each segway, I get the overlap data from its own chrom,
    # and I get the overlap data from all other chroms.
    for nonSelfAccession in nonKeys:

        #print(nonSelfAccession)

        c = annAccessionList.index(nonSelfAccession)
        #print(c)

        sumCovVal = allMatchThis[1][nonSelfAccession]
        book = np.argsort(sumCovVal)[::-1]

        topInds = book[0:3]
        fracs = allMatchThis[2][nonSelfAccession]
        #print('coverage with the SELF label for NONSELF')
        #print(fracs[topIndsSelf[0]])
        #print(sum(fracs[topIndsSelf]))

        thisLabel = labels[topInds[0]]
        #print(thisLabel)
        thisTerm = thisLabel.split('_')[1]
        termInd = segwayLabels.index(thisTerm)

        labelColor[s,c] = termInd
        labelCluster[s,c] = thisLabel.split('_')[0]
        labelCoverage[s,c] = fracs[topInds[0]]
        labelCovOther[s,c] = fracs[topIndsSelf[0]]
        labelGenomeCover[s,c] = float(thisLabel.split('_')[2])
        overlapLog[s,c] = allMatchThis[3][nonSelfAccession][topInds[0]]
        #print('coverage with the NONSELF label')
        #print(fracs[topInds[0]])
        #print(sum(fracs[topInds]))

        minMeanLogNonSelf = (allMatchThis[3][nonSelfAccession][topInds])
        #print(minMeanLogNonSelf)

        #print(selfMatchThis[3][topIndsSelf[0]])

        #for ind in topInds:
        #    print(labels[ind])

        #print('----------------')
        otherCov[nonSelfAccession] = sum(fracs[topInds])

    allCov[annAccession] = otherCov


annAccession = annAccessionList[6]    
otherCov = list(allCov[annAccession].values())
mainCov = selfCov[annAccession]

sib = np.sort(otherCov/mainCov)

plt.hist(sib)
plt.show()
sns.color_palette("tab10")

gyr = ['#FFFF00','#FFC34D', '#FF0000', '#FF4500', '#008000','#940A9B' ,'#66CDAA' ,'#BDB76B' ,'#C0C0C0', '#8A91D0', '#FFFFFF']
myColors= sns.color_palette(gyr)
from matplotlib.colors import LinearSegmentedColormap

cmap = LinearSegmentedColormap.from_list('Custom', myColors, len(myColors))

labelColor = labelColor[0:30, :]
dellc = np.delete(labelColor, [5,19], 0)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
dellc2 = np.delete(dellc, sib, 1)
sns.heatmap(dellc2[0:28, 0:28], cmap=cmap)
sns.heatmap(labelColor[0:28, 0:28], cmap=cmap)
sns.heatmap(dellc[0:28, 0:28], cmap=cmap)
plt.show()

cov = labelCoverage[0:30, :]
delcov = np.delete(cov, [5,19], 0)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
delcov2 = np.delete(delcov, sib, 1)
sns.heatmap(delcov2[0:28, 0:28])
plt.show()

covo = labelCovOther[0:30, :]
delcovo = np.delete(covo, [5,19], 0)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
delcovo2 = np.delete(delcovo, sib, 1)
delcovo2[np.where(delcovo2 > .5)] = .5
sns.heatmap(delcovo2[0:28, 0:28])
plt.show()

plt.boxplot(np.diag(delcovo2[0:28, 0:28]))
plt.show() # give me the specific log ratio overlap
# TODO: I want to say we recover # this percentage of the enhancers labels with a specific overlap

lclust = labelCluster[0:30, :]
dellclust = np.delete(lclust, [5,19], 1)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
dellclust2 = np.delete(dellclust, sib, 0)
#delcovo2[np.where(delcovo2 > .5)] = .5
sns.heatmap(dellclust2[0:28, 0:28], annot=True, cmap='Paired')
plt.show()

lgc = labelGenomeCover[0:30, :]
dellgc = np.delete(lgc, [5,19], 1)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
dellgc2 = np.delete(dellgc, sib, 0)
#delcovo2[np.where(delcovo2 > .5)] = .5
sns.heatmap(dellgc2[0:28, 0:28], annot=True, fmt='.2f')
plt.show()


oll = overlapLog[0:30, :]
deloll = np.delete(oll, [5,19], 1)
sib = [ 5, 19, 31, 58, 69, 81, 83, 96, 97]
deloll2 = np.delete(deloll, sib, 0)
#delcovo2[np.where(delcovo2 > .5)] = .5
sns.heatmap(deloll2[0:28, 0:28])
plt.show()



fig, axs = plt.subplots(3, 2, figsize=(10,14))

s1= sns.heatmap(dellclust2[0:28, 0:28], cmap='Paired', ax=axs[0,0])
s1.set_title('cluster ID for the best match label')
#sns.heatmap(labelCluster[0:30, 0:30], annot=True, cmap='Paired', ax=axs[1])
s2=sns.heatmap(dellc2[0:28, 0:28], cmap=cmap, ax=axs[0,1])
s2.set_title('cluster type for the best match label- ENCODE colors')
#sns.heatmap(dellgc2[0:28, 0:28], annot=True, fmt='.2f', ax=axs[1,1])
s3=sns.heatmap(dellgc2[0:28, 0:28], ax=axs[1,0])
s3.set_title('genome coverage of the best match label')
s4=sns.heatmap(delcov2[0:28, 0:28], ax=axs[1,1])
s4.set_title('enhancer region coverage for the best match label')
s5=sns.heatmap(deloll2[0:28, 0:28], ax=axs[2,0])
s5.set_title('log obs over expected for the best match label')
s6=sns.heatmap(delcovo2[0:28, 0:28], ax=axs[2,1])
s6.set_title('coverage of the enhancer region by the diagonal label')
plt.show()

# TODO: what coverage do I get at that same level of significance (log ratio overlap)?
# regarding the coverage, level of significance doe snot matter, as a Quies might have high significance level
# for the other samples, since, it is the other sample!!! BUT, where it is an active lable, we definitley have lower
# significance level for the other thing. That is why it doesn't matter

# TODO: document the whole process you did here. 
