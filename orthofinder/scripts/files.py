#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2016 David Emms
#
# This program (OrthoFinder) is distributed under the terms of the GNU General Public License v3
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  
#  When publishing work that uses OrthoFinder please cite:
#      Emms, D.M. and Kelly, S. (2015) OrthoFinder: solving fundamental biases in whole genome comparisons dramatically 
#      improves orthogroup inference accuracy, Genome Biology 16:157
#
# For any enquiries send an email to David Emms
# david_emms@hotmail.comhor: david


"""
Handles location of all input and output files

Either way, first step is to call (old directory structure) one of:

    CreateOutputDirFromExistingDirs
    CreateOutputDirFromStart_old       - this will be removed soon
    CreateOutputDirFromTrees
    
For (new directory structure) __Files_new_dont_manually_create__ the options are:
    CreateOutputDirFromStart_new
    CreateOutputDirFromExistingDirs
    CreateOutputDirFromTrees
    
These options are all about working out where the old files are, they are for the InputFilesLocator classes:
InputFilesLocator_old
InputFilesLocator_new

"""
import os
import sys
import glob
import time
import shutil
import datetime

import util

class SpeciesInfo(object):
    def __init__(self):
        self.speciesToUse = []           #       seqsInfo.iSpeciesToUse   - which to include for this analysis 
        self.nSpAll = None               #       seqsInfo.nSpAll => 0, 1, ..., nSpAll - 1 are valid species indices
        self.iFirstNewSpecies = None     #       iFirstNew   => (0, 1, ..., iFirstNew-1) are from previous and (iFirstNew, iFirstNew+1, ..., nSpecies-1) are the new species indices
    def __str__(self):
        return str((self.speciesToUse, self.nSpAll, self.iFirstNewSpecies))

def IsNewDirStructure(inputDir):
    return os.path.exists(inputDir + "/Log.txt")
    
def IsWorkingDirectory(orthofinderWorkingDir):
    ok = True
    ok = ok and len(glob.glob(orthofinderWorkingDir + "clusters_OrthoFinder_*.txt_id_pairs.txt")) > 0
    ok = ok and len(glob.glob(orthofinderWorkingDir + "Species*.fa")) > 0
    return ok

""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """
                    
class __Files_new_dont_manually_create__(object):    
    def __init__(self):
        self.baseOgFormat = "OG%07d"
        self.wd_base = None             # Base: blast, species & sequence IDs, species fasta files - should not request this and then write here
        self.wd_current = None          # Location to write out any new files
        self.wd_trees = None            # Location of working dir containing tree files 
        self.rd1 = None
        self.fileIdentifierString = "OrthoFinder"
        self.clustersFilename = None
        self.iResultsVersion = None
        self.nondefaultPickleDir = None
        self.speciesTreeRootedIDsFN = None
        self.multipleRootedSpeciesTreesDir = None
        # to be modified as appropriate
        self.align_dir_name = "Alignments/"
        self.align_dir_name = "MultipleSequenceAlignments/"
     
    """ ========================================================================================== """
    # RefactorDS - FileHandler
    def CreateOutputDirFromStart_new(self, fasta_dir, base, append_name = ""):
        """
        The intial difference will be that results will go in OrthoFinder/Results_DATE or USER_SPECIFIED/RESULTS_DATE
        whereas before they went in Results_DATE or USER_SPECIFIED.
        
        Question, what if there is an OrthoFinder directory in fasta_dir already?
        Options:
            - * Use the same one? In which case WorkingDir must be kept completely separate. ANS. Yes, design is that correct files are identified
            - Create a new one?
        """
        self.rd1, self.wd_current = util.CreateNewPairedDirectories(base + "Results_" + ("" if append_name == "" else append_name + "_"), base + "WorkingDirectory_" + ("" if append_name == "" else append_name + "_"))
        self.wd_base = self.wd_current
        self.wd_trees = self.wd_base
        print(self.rd1, self.wd_current)
        with open(self.rd1 + "Log.txt", 'wb'), open(self.wd_current + "Log.txt", 'wb'):
            pass
        self.StartLog()
        
    # RefactorDS - PreviousFilesLocator
    def StartFromOrthogroupsOrSequenceSearch(self, wd_base, base, clustersFilename_pairs=None, append_name = "", userSpeciesTree=None):
        """
        NEed to initialise:
        wd_base
        wd_trees
        wd_current
        """
        if self.wd_base != None: raise Exception("Changing WorkingDirectory1")
        self.wd_base = wd_base
        if clustersFilename_pairs != None: self.clustersFilename = clustersFilename_pairs[:-len("_id_pairs.txt")]
        self.rd1, self.wd_current = util.CreateNewPairedDirectories(base + "Results_" + ("" if append_name == "" else append_name + "_"), base + "WorkingDirectory_" + ("" if append_name == "" else append_name + "_"))
        with open(self.rd1 + "Log.txt", 'wb'), open(self.wd_current + "Log.txt", 'wb'):
            pass
        self.wd_trees = self.wd_current
        self.StartLog()
    
    
    def StartFromTrees(self, 
                       wd1, 
                       wd2,
                       base, 
                       clustersFilename_pairs, 
                       append_name=None,
                       speciesTreeFN=None):
        self.wd_base = wd1
        self.wd_trees = wd2
        self.rd1, self.wd_current = util.CreateNewPairedDirectories(base + "Results_" + ("" if append_name == "" else append_name + "_"), base + "WorkingDirectory_" + ("" if append_name == "" else append_name + "_"))
        self.rd2 = self.rd1
        self.clustersFilename = clustersFilename_pairs[:-len("_id_pairs.txt")]
        self.StartLog()
        self.WriteToLog("Species Tree: %s\n" % self.speciesTreeRootedIDsFN)
                                         
    # RefactorDS - this should just be the initialiser
    def CreateOutputDirectories(self, options, previous_files_locator, base_dir, fastaDir=None):
        """
        previous_files_locator should be able to return:
        From Blast:
            GetWD1()
        FromGroups:
            GetWD1()
            GetHomeForResults()   <--- This doesn't seem to make sense
            clustersFilename_pairs
        From Trees:
            GetWD1()
            GetWDTrees()
            clustersFilename_pairs
            GetSpeciesTreeFN()
        """
        
        if options.qStartFromBlast: 
            # RefactorDS - previously, checked if we wanted old or new
            self.StartFromOrthogroupsOrSequenceSearch(previous_files_locator.GetWD1(), 
                                                      base_dir,
                                                      append_name=options.name)   # for new structure
#            self.CreateOutputDirFromExistingDirs(workingDir) # for old
        elif options.qStartFromTrees:
            self.StartFromTrees(previous_files_locator.GetWD1(), 
                                previous_files_locator.GetWDTrees(),
                                base_dir, 
                                previous_files_locator.clustersFilename_pairs, 
                                options.name,
                                options.speciesTreeFN if options.speciesTreeFN != None else previous_files_locator.GetSpeciesTreeFN())
#            self.CreateOutputDirFromTrees(orthologuesDir, options.speciesTreeFN)
        elif options.qStartFromFasta:
            # But, by previous condition, not qStartFromBlast
            self.CreateOutputDirFromStart_new(fastaDir, base_dir, append_name=options.name)
        elif options.qStartFromGroups:
            self.StartFromOrthogroupsOrSequenceSearch(previous_files_locator.GetWD1(), 
#                                      previous_files_locator.GetHomeForResults(),
                                      base_dir,
                                      previous_files_locator.clustersFilename_pairs, 
                                      append_name=options.name)
    """ ========================================================================================== """
       
    # RefactorDS - FileHandler
    def SetNondefaultPickleDir(self, d):
        self.pickleDir = d
   
    def GetPickleDir(self):
        if self.nondefaultPickleDir != None: 
            d = self.pickleDir
        else:
            d = self.wd_current + "pickle/"
        if not os.path.exists(d): os.mkdir(d)
        return d
   
#    # RefactorDS - FileHandler
#    def MakeResultsDirectory2(self, tree_generation_method, stop_after="", append_name=""):
#        """
#        Args
#        tree_method: msa, dendroblast, phyldog (determines the directory structure that will be created)
#        stop_after: seqs, align
#        """
#        if self.rd1 == None: raise Exception("No rd1") 
#        self.rd2 = util.CreateNewWorkingDirectory(self.GetResultsDirectory1() + "Orthologues_" + ("" if append_name == "" else append_name + "_"))   
#        self.wd2 = self.rd2 + "WorkingDirectory/"
#        os.mkdir(self.wd2)
#        os.mkdir(self.rd2 + "Orthologues/")
#        if tree_generation_method == "msa":
#            for i, d in enumerate([self.rd2 + "Sequences/", self.wd2 + "Sequences_ids/", self.rd2 + self.align_dir_name, self.wd2 + "Alignments_ids/", self.rd2 + "Gene_Trees/", self.wd2 + "Trees_ids/"]):
#                if stop_after == "seqs" and i == 2: break 
#                if stop_after == "align" and i == 4: break 
#                if not os.path.exists(d): os.mkdir(d)
#        elif tree_generation_method == "dendroblast":
#            for i, d in enumerate([self.wd2 + "Distances/", self.rd2 + "Gene_Trees/", self.wd2 + "Trees_ids/"]):
#                if not os.path.exists(d): os.mkdir(d)
         
    """ Standard Methods
        ========================================================================================== """               
    def WriteToLog(self, text, qWithTime=False):
        pass
        
    def LogSpecies(self):
        text = "Species used: \n"
        fn = self.GetSpeciesIDsFN()
        with open(fn, 'rb') as infile:
            text += "".join(infile.readlines())
        self.WriteToLog(text + "\n")
        
    """ Standard Dirctories
        ========================================================================================== """
    
    def GetWorkingDirectory1_Read(self):
        if self.wd_base == None: raise Exception("No wd1")
        return self.wd_base 
        
    def GetWorkingDirectory_Write(self):
        if self.wd_current == None: raise Exception("No wd_current")
        return self.wd_current 
        
    def GetResultsDirectory1(self):
        if self.rd1 == None: raise Exception("No rd1")
        return self.rd1 
        
    def GetResultsDirectory2(self):
        if self.rd2 == None: raise Exception("No rd2")
        return self.rd2 
        
    def GetOrthologuesDirectory(self):
        """"Where the directories of species orthologues are"""
        if self.rd2 == None: raise Exception("No rd2")
        d = self.rd2 + "Orthologues/"
        if not os.path.exists(d): os.mkdir(d)
        return d
        
    """ Orthogroups files 
        ========================================================================================== """
        
    def GetSpeciesIDsFN(self):
        if self.wd_base == None: raise Exception("No wd1")
        print(self.wd_base + "SpeciesIDs.txt")
        return self.wd_base + "SpeciesIDs.txt"
        
    def GetSequenceIDsFN(self):
        if self.wd_base == None: raise Exception("No wd1")
        return self.wd_base + "SequenceIDs.txt"
        
    def GetSpeciesSeqsDir(self):
        if self.wd_base == None: raise Exception("No wd1")
        return self.wd_base 
        
    def GetSpeciesFastaFN(self, iSpecies):
        if self.wd_base == None: raise Exception("No wd1")
        return "%sSpecies%d.fa" % (self.wd_base, iSpecies)
        
    def GetSortedSpeciesFastaFiles(self):
        if self.wd_base == None: raise Exception("No wd1")
        fastaFilenames = glob.glob(self.wd_base + "Species*.fa")
        speciesIndices = []
        for f in fastaFilenames:
            start = f.rfind("Species")
            speciesIndices.append(int(f[start+7:-3]))
        indices, sortedFasta = util.SortArrayPairByFirst(speciesIndices, fastaFilenames)
        return sortedFasta  
        
    def GetSpeciesDatabaseN(self, iSpecies, program="Blast"):
        if self.wd_base == None: raise Exception("No wd1")
        return "%s%sDBSpecies%d" % (self.wd_base, program, iSpecies)
        
    def GetBlastResultsDir(self):
        return self.wd_base
        
    def GetBlastResultsFN(self, iSpeciesSearch, jSpeciesDB):
        if self.wd_base == None: raise Exception("No wd1")
        return "%sBlast%d_%d.txt" % (self.wd_base, iSpeciesSearch, jSpeciesDB)
        
    def GetGraphFilename(self):
        if self.wd_current == None: raise Exception("No wd_current")
        return self.wd_current + "%s_graph.txt" % self.fileIdentifierString
        
    def CreateUnusedClustersFN(self, mclInflation):
        if self.wd_current == None: raise Exception("No wd_current")
        self.clustersFilename, self.iResultsVersion = util.GetUnusedFilename(self.wd_current  + "clusters_%s_I%0.1f" % (self.fileIdentifierString, mclInflation), ".txt")
        return self.clustersFilename, self.clustersFilename + "_id_pairs.txt"
        
    def SetClustersFN(self, pairsFN):
        self.clustersFilename = pairsFN[:-len("_id_pairs.txt")]
        log = "Orthogroups used: %s\n\n" % self.clustersFilename
        self.WriteToLog(log)
        
    def GetClustersFN(self):
        return self.clustersFilename + "_id_pairs.txt"
        
    def GetResultsFNBase(self):
        if self.rd1 == None: 
            raise Exception("No rd1")
        if self.iResultsVersion == None:
            raise Exception("Base results identifier has not been created")
        return self.rd1 + "Orthogroups" + ("" if self.iResultsVersion == 0 else "_%d" % self.iResultsVersion)
        
    def GetOGsStatsResultsDirectory(self):
        return self.GetResultsDirectory1() 
        
    """ Orthologues files
        ========================================================================================== """
        
    def GetResultsSeqsDir(self):
        return self.rd2 + "Sequences/"
        
    def GetResultsAlignDir(self):
        return self.align_dir_name
        
    def GetResultsTreesDir(self):
        return self.rd2 + "Gene_Trees/"
        
    def GetOlogStatsDir(self):
        return self.rd2
    
    def GetSuspectGenesDir(self):
        d = self.rd2 + "Phylogenetically_Misplaced_Genes/"
        if not os.path.exists(d): os.mkdir(d)
        return d
        
    def GetPutativeXenelogsDir(self):
        d = self.rd2 + "Putative_Xenologues/"
        if not os.path.exists(d): os.mkdir(d)
        return d
    
    def GetOGsSeqFN(self, iOG, qResults=False):
        if qResults:
            return self.rd2 + "Sequences/" + (self.baseOgFormat % iOG) + ".fa"
        else:
            return self.wd_current + "Sequences_ids/" + (self.baseOgFormat % iOG) + ".fa"
            
    def GetOGsAlignFN(self, iOG, qResults=False):
        if qResults:
            return self.align_dir_name + (self.baseOgFormat % iOG) + ".fa"
        else:
            return self.wd_current + "Alignments_ids/" + (self.baseOgFormat % iOG) + ".fa"
            
    def GetOGsTreeFN(self, iOG, qResults=False):
        if qResults:
            return self.rd2 + "Gene_Trees/" + (self.baseOgFormat % iOG) + "_tree.txt"
        else:
            return self.wd_current + "Trees_ids/" + (self.baseOgFormat % iOG) + "_tree_id.txt"   
        
    def GetSpeciesTreeConcatAlignFN(self, qResults=False):
        if qResults:
            return self.align_dir_name + "SpeciesTreeAlignment.fa"
        else:
            return self.wd_current + "Alignments_ids/SpeciesTreeAlignment.fa"  
        
    def GetSpeciesTreeMatrixFN(self, qPutInWorkingDir = False):
        if qPutInWorkingDir:
            return self.wd_current + "SpeciesMatrix.phy"
        else:
            return self.wd_current + "Distances/SpeciesMatrix.phy"
            
    def GetSpeciesTreeUnrootedFN(self, qAccessions=False):
        if qAccessions:
            return self.wd_trees + "SpeciesTree_unrooted.txt"
        else: 
            return self.wd_trees + "Trees_ids/SpeciesTree_unrooted_id.txt"  
            
    def SetSpeciesTreeIDsRootedFN(self, fn):
        self.speciesTreeRootedIDsFN = fn
            
    def GetSpeciesTreeIDsRootedFN(self):
        return self.speciesTreeRootedIDsFN
        
    def GetSpeciesTreeResultsFN(self, i, qUnique):
        """
        The results species tree (rooted, accessions, support values)
        i: index for species tree, starting at 0
        qUnique: bool, has a unique root been identified (as it may not be known exatly which branch the root belongs on)
        E.g. if there were just one species tree, the correct call would be GetSpeciesTreeResultsFN(0,True)
        """
        if qUnique:
            return self.rd2 + "SpeciesTree_rooted.txt"
        else:
            if not self.multipleRootedSpeciesTreesDir:
                self.multipleRootedSpeciesTreesDir = self.rd2 + "Potential_Rooted_Species_Trees/"
                if not os.path.exists(self.multipleRootedSpeciesTreesDir): os.mkdir(self.multipleRootedSpeciesTreesDir)
            return self.multipleRootedSpeciesTreesDir + "SpeciesTree_rooted_at_outgroup_%d.txt" % i
        
    def GetSpeciesTreeUserSupplied_idsFN(self):
        return self.wd_current + "SpeciesTree_UserSupplied_Rooted_IDs.txt"
        
    def GetOGsDistMatFN(self, iOG):
        return self.wd_current + "Distances/OG%07d.phy" % iOG
        
    def GetSpeciesDict(self):
        d = util.FullAccession(self.GetSpeciesIDsFN()).GetIDToNameDict()
        return {k:v.rsplit(".",1)[0] for k,v in d.items()}
        
    """ ========================================================================================== """
            
    def GetOGsTreeDir(self, qResults=False):
        if qResults:
            return self.rd2 + "Gene_Trees/" 
        else:
            return self.wd_trees + "Trees_ids/" 
            
    def GetOGsReconTreeDir(self, qResults=False):
        if qResults:
            d = self.rd2 + "Resolved_Gene_Trees/" 
            if not os.path.exists(d): os.mkdir(d)
            return d
        else:
            raise NotImplemented() 
            
    def GetOGsReconTreeFN(self, iOG):
        return self.rd2 + "Resolved_Gene_Trees/OG%07d_tree.txt" % iOG
            
    def GetPhyldogWorkingDirectory(self):
        d = self.wd_current + "phyldog/"
        if not os.path.exists(d): os.mkdir(d)
        return d
            
    def GetPhyldogOGResultsTreeFN(self, i):
        return self.wd_current + "phyldog/OG%07d.ReconciledTree.txt" % i
            
    def GetDuplicationsFN(self):
        return self.rd2 + "Duplications.csv"
        
    
    """ ========================================================================================== """
         
    def CleanWorkingDir2(self):
        dirs = ['Distances/']
        for d in dirs:
            dFull = self.wd_current + d
            if os.path.exists(dFull): 
                try:
                    shutil.rmtree(dFull)
                except OSError:
                    time.sleep(1)
                    shutil.rmtree(dFull, True)  # shutil / NFS bug - ignore errors, it's less crucial that the files are deleted
                    
    """ ************************************************************************************************************************* """

#    def CreateFromScratch(self, results_base, wd_blast, speciesTreeFN=None):
#        pass
#    
#    def CreateFromBlast(self, results_base, wd_blast, speciesTreeFN=None):
#        pass
#    
#    def CreateFromOGs(self, results_base, wd_blast, wd_ogs, speciesTreeFN=None):
#        pass
#    
#    def CreateFromTrees(self, results_base, wd_blast, wd_ogs, wd_trees, speciesTreeFN=None):
#        pass

            
# RefactorDS - FileHandler 
    """ Standard Methods ========================================================================================== """               
    def WriteToLog(self, text, qWithTime=False):
        prepend = ""
        if qWithTime:
            prepend = str(datetime.datetime.now()).rsplit(".", 1)[0] + " : "
        with open(self.rd1 + "Log.txt", 'ab') as outfile:
            outfile.write(prepend + text)
    
    def StartLog(self):
        self.WriteToLog("Started OrthoFinder version " + util.version + "\n", True)
        text = "Command Line: " + " ".join(sys.argv) + "\n\n"
        text += "WorkingDirectory_Base: %s\n" % self.wd_base
        if self.clustersFilename != None: text += "Orthogroups: %s\n" % self.clustersFilename
        self.WriteToLog(text)
    
    def LogWorkingDirectoryOGs(self, qCreatedThisRun):
        if qCreatedThisRun:
            self.WriteToLog("WorkingDirectory_OGs: %s\n" % self.wd_current)
        else:
            self.WriteToLog("WorkingDirectory_OGs: %s\n" % self.wd_base)
    
    def LogWorkingDirectoryTrees(self):
        self.WriteToLog("WorkingDirectory_Trees: %s\n" % self.wd2)
        
    def MakeResultsDirectory2(self, tree_generation_method, stop_after="", append_name=""):
        """
        Args
        tree_method: msa, dendroblast, phyldog (determines the directory structure that will be created)
        stop_after: seqs, align
        """
        # RefactorDS - need to change where it puts things
        print("**** MakeResultsDirectory2 ****")
        if self.rd1 == None: raise Exception("No rd1") 
        self.rd2 = self.rd1   
        self.wd2 = self.wd_current 
        self.wd_trees = self.wd_current
        os.mkdir(self.rd2 + "Orthologues/")
        if tree_generation_method == "msa":
            for i, d in enumerate([self.rd2 + "Sequences/", self.wd_current + "Sequences_ids/", self.rd2 + self.align_dir_name, self.wd_current + "Alignments_ids/", self.rd2 + "Gene_Trees/", self.wd_current + "Trees_ids/"]):
                if stop_after == "seqs" and i == 2: break 
                if stop_after == "align" and i == 4: break 
                if not os.path.exists(d): os.mkdir(d)
        elif tree_generation_method == "dendroblast":
            for i, d in enumerate([self.wd_current + "Distances/", self.rd2 + "Gene_Trees/", self.wd_current + "Trees_ids/"]):
                print(d)
                if not os.path.exists(d): os.mkdir(d)
    
    def GetResultsFNBase(self):
        if self.rd1 == None: 
            raise Exception("No rd1")
        if self.iResultsVersion == None:
            raise Exception("Base results identifier has not been created")
        d = self.rd1 + "Orthogroups/"
        if not os.path.exists(d): os.mkdir(d)
        return d + "Orthogroups" + ("" if self.iResultsVersion == 0 else "_%d" % self.iResultsVersion)
        
    def GetOGsStatsResultsDirectory(self):
        d = self.rd1 + "Comparative_Genomics_Statistics/"
        if not os.path.exists(d): os.mkdir(d)
        return d
        
    def GetDuplicationsFN(self):
        d = self.rd1 + "Gene_Duplication_Events/"
        if not os.path.exists(d): os.mkdir(d)
        return d + "Duplications.csv"
        
    def GetPutativeXenelogsDir(self):
        d = self.rd2 + "Phylogenetically_Misplaced_Genes/"
        if not os.path.exists(d): os.mkdir(d)
        return d
        
    def GetOlogStatsDir(self):
        return self.GetOGsStatsResultsDirectory()
    
            
    def GetSpeciesTreeResultsFN(self, i, qUnique):
        """
        The results species tree (rooted, accessions, support values)
        i: index for species tree, starting at 0
        qUnique: bool, has a unique root been identified (as it may not be known exatly which branch the root belongs on)
        E.g. if there were just one species tree, the correct call would be GetSpeciesTreeResultsFN(0,True)
        """
        d = self.rd2 + "Species_Tree/"
        if not os.path.exists(d): os.mkdir(d)
        if qUnique:
            return d + "SpeciesTree_rooted.txt"
        else:
            if not self.multipleRootedSpeciesTreesDir:
                self.multipleRootedSpeciesTreesDir = d + "Potential_Rooted_Species_Trees/"
                if not os.path.exists(self.multipleRootedSpeciesTreesDir): os.mkdir(self.multipleRootedSpeciesTreesDir)
            return self.multipleRootedSpeciesTreesDir + "SpeciesTree_rooted_at_outgroup_%d.txt" % i    



FileHandler = __Files_new_dont_manually_create__()
                    
""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """

class Unprocessable(Exception):
    pass

class PreviousFilesLocator(object):
    def __init__(self, options, continuationDir):
        if not continuationDir.endswith("/"): continuationDir += "/"
        self.home_for_results = continuationDir + "../"
        self.wd_base = None
        if (options.qStartFromFasta and not options.qStartFromBlast):
            # there are no files to find
            return
        if not IsNewDirStructure(continuationDir): raise Unprocessable("Input directory structure is not processable as new structure")
        self.ProcessLog(continuationDir + "/Log.txt")
        if options.qStartFromGroups:
            pass
        else:
            raise NotImplementedError
        
    def ProcessLog(self, logFN):
        """
        Get all relevant data from log file. 
        Checks the paths ssaved do exist still
        Should work with relevant paths to allow directory to move
        Other methods can then check that the data required for a particualr run is available
        """
        with open(logFN, 'rb') as infile:
            for line in infile:
                wd_base = "WorkingDirectory_OGs: "
                wd_trees = "WorkingDirectory_Trees: "
                if line.startswith(wd_base): 
                    self.wd_base = line.rstrip()[len(wd_base):]
                    if not os.path.exists(self.wd_base):
                        # try to see if it's a relative directory to current one
                        self.wd_base = os.path.split(logFN)[0] + "/../" + os.path.split(self.wd_base[:-1])[1] + "/"
                        if not os.path.exists(self.wd_base):
                            print("ERROR: Missing directory: %s" % self.wd_base)
                            util.Fail()
                    self.GetOGsFile()
                if line.startswith(wd_trees): 
                    self.wd_trees = line.rstrip()[len(wd_trees):]
                    if not os.path.exists(self.wd_trees):
                        # try to see if it's a relative directory to current one
                        self.wd_base = os.path.split(logFN)[0] + "/../" + os.path.split(self.wd_trees[:-1])[1] + "/"
                        if not os.path.exists(self.wd_trees):
                            print("ERROR: Missing directory: %s" % self.wd_trees)
                            util.Fail()
            
    def GetOGsFile(self):
        """returns the WorkingDirectory, ResultsDirectory and clusters_id_pairs filename"""
        clustersFiles = glob.glob(self.wd_base + "clusters_OrthoFinder_*.txt_id_pairs.txt")
        if len(clustersFiles) == 0:
            print("ERROR: Didn't find a clusters_OrthoFinder_*.txt_id_pairs.txt file in " + self.wd_base)
            util.Fail()
        if len(clustersFiles) > 1:
            print("ERROR: Found more than one clusters_OrthoFinder_*.txt_id_pairs.txt files")
            util.Fail()
        self.clustersFilename_pairs = clustersFiles[0] 

    def GetWD1(self):
        return self.wd_base
        
    def GetHomeForResults(self):
        return self.home_for_results
        
    
""" ************************************************************************************************************************* """

class PreviousFilesLocator_old(PreviousFilesLocator):
    def __init__(self, options, continuationDir):
        if not continuationDir.endswith("/"): continuationDir += "/"
        self.baseOgFormat = "OG%07d"
        self.wd_base = None
        self.continuationDir = continuationDir
        self.rd1 = None
        self.clustersFilename = None
        self.iResultsVersion = None
        self.nondefaultPickleDir = None
        self.speciesTreeRootedIDsFN = None
        self.multipleRootedSpeciesTreesDir = None
        # to be modified as appropriate
        self.align_dir_name = "Alignments/"
        
        if options.qStartFromGroups or options.qStartFromTrees:
            # User can specify it using clusters_id_pairs file, process this first to get the workingDirectory
            ogs_dir = continuationDir + "../" if options.qStartFromTrees else continuationDir
            self.wd_base, self.orthofinderResultsDir, self.clustersFilename_pairs = self.GetOGsFile(ogs_dir)
            print("\nFound OGs files")
            print(self.wd_base, self.orthofinderResultsDir, self.clustersFilename_pairs)
            if options.qStartFromTrees:
                self.FindFromTrees(continuationDir, options.speciesTreeFN)
        elif options.qStartFromBlast:
            if IsWorkingDirectory(continuationDir): 
                self.wd_base = continuationDir
            elif IsWorkingDirectory(continuationDir + "WorkingDirectory/"):
                self.wd_base = continuationDir + "WorkingDirectory/"
            else:
                self.wd_base = continuationDir   # nothing much to do, set this as the one to try and fail later
                
                
    def GetOGsFile(self, userArg):
        """returns the WorkingDirectory, ResultsDirectory and clusters_id_pairs filename"""
        qSpecifiedResultsFile = False
        if userArg == None:
            print("ERROR: orthofinder_results_directory has not been specified")
            util.Fail()
        if os.path.isfile(userArg):
            fn = os.path.split(userArg)[1]
            if ("clusters_OrthoFinder_" not in fn) or ("txt_id_pairs.txt" not in fn):
                print("ERROR:\n    %s\nis neither a directory or a clusters_OrthoFinder_*.txt_id_pairs.txt file." % userArg)
                util.Fail()
            qSpecifiedResultsFile = True
            # user has specified specific results file
        elif userArg[-1] != os.path.sep: 
            userArg += os.path.sep
        
        # find required files
        if qSpecifiedResultsFile:
            orthofinderWorkingDir = os.path.split(userArg)[0] + os.sep
            if not IsWorkingDirectory(orthofinderWorkingDir):
                print("ERROR: cannot find files from OrthoFinder run in directory:\n   %s" % orthofinderWorkingDir)
                util.Fail()
        else:
            orthofinderWorkingDir = os.path.split(userArg)[0] if qSpecifiedResultsFile else userArg
            if not IsWorkingDirectory(orthofinderWorkingDir):
                orthofinderWorkingDir = userArg + "WorkingDirectory" + os.sep   
                if not IsWorkingDirectory(orthofinderWorkingDir):
                    print("ERROR: cannot find files from OrthoFinder run in directory:\n   %s\nor\n   %s\n" % (userArg, orthofinderWorkingDir))
                    util.Fail()
                
        if qSpecifiedResultsFile:
            print("\nUsing orthogroups in file:\n    %s" % userArg)
            return orthofinderWorkingDir, orthofinderWorkingDir, userArg
        else:     
            # identify orthogroups file
            clustersFiles = glob.glob(orthofinderWorkingDir + "clusters_OrthoFinder_*.txt_id_pairs.txt")
            orthogroupFiles = glob.glob(orthofinderWorkingDir + "OrthologousGroups*.txt") + glob.glob(orthofinderWorkingDir + "Orthogroups*.txt")
            if orthofinderWorkingDir != userArg:
                orthogroupFiles += glob.glob(userArg + "OrthologousGroups*.txt")
                orthogroupFiles += glob.glob(userArg + "Orthogroups*.txt")
            # User may have specified a WorkingDirectory and results could be in directory above
            if len(orthogroupFiles) < len(clustersFiles):
                orthogroupFiles += glob.glob(userArg + ".." + os.sep + "OrthologousGroups*.txt")
                orthogroupFiles += glob.glob(userArg + ".." + os.sep + "Orthogroups*.txt")
            clustersFiles = sorted(clustersFiles)
            orthogroupFiles = sorted(orthogroupFiles)
            if len(clustersFiles) > 1 or len(orthogroupFiles) > 1:
                print("ERROR: Results from multiple OrthoFinder runs found\n")
                print("Tab-delimiter Orthogroups*.txt/OrthologousGroups*.txt files:")
                for fn in orthogroupFiles:
                    print("    " + fn)
                print("With corresponding cluster files:")
                for fn in clustersFiles:
                    print("    " + fn)
                print("\nPlease run with only one set of results in directories or specifiy the specific clusters_OrthoFinder_*.txt_id_pairs.txt file on the command line")
                util.Fail()        
                
            if len(clustersFiles) != 1 or len(orthogroupFiles) != 1:
                print("ERROR: Results not found in <orthofinder_results_directory> or <orthofinder_results_directory>/WorkingDirectory")
                print("\nCould not find:\n    Orthogroups*.txt/OrthologousGroups*.txt\nor\n    clusters_OrthoFinder_*.txt_id_pairs.txt")
                util.Fail()
                
            print("\nUsing orthogroups in file:\n    %s" % orthogroupFiles[0])
            print("and corresponding clusters file:\n    %s" % clustersFiles[0])
            return orthofinderWorkingDir, userArg, clustersFiles[0]
            
    def FindFromTrees(self, orthologuesDir, userSpeciesTree):
        """
        if userSpeciesTree == None: Use existing tree
        """
        print("\nFind from trees:")
        print((orthologuesDir, userSpeciesTree))
        self.rd2 = self.rd1
        self.wd2 = orthologuesDir + "WorkingDirectory/"
        # Find species tree
        if userSpeciesTree == None:
            possibilities = ["SpeciesTree_ids_0_rooted.txt", "SpeciesTree_ids_1_rooted.txt", "SpeciesTree_user_ids.txt", "SpeciesTree_unrooted_0_rooted.txt", "STAG_SpeciesTree_ids_0_rooted.txt"] # etc (only need to determine if unique)
            nTrees = 0
            for p in possibilities:
                for d in [self.wd2, self.wd2 + "Trees_ids/"]:
                    fn = d + p
                    if os.path.exists(fn): 
                        nTrees += 1
                        speciesTree_fn = fn
            if nTrees == 0:
                print("\nERROR: There is a problem with the specified directory. The rooted species tree %s or %s is not present." % (possibilities[0], possibilities[2]))
                print("Please rectify the problem or alternatively use the -s option to specify the species tree to use.\n")
                util.Fail()
            if nTrees > 1:
                print("\nERROR: There is more than one rooted species tree in the specified directory structure. Please use the -s option to specify which species tree should be used\n")
                util.Fail()
            self.speciesTreeRootedIDsFN = speciesTree_fn
        else:
            if not os.path.exists(userSpeciesTree):
                print("\nERROR: %s does not exist\n" % userSpeciesTree)
                util.Fail()
            self.speciesTreeRootedIDsFN = userSpeciesTree
                
    def GetHomeForResults(self):
        return self.continuationDir + "OrthoFinder/"

    def GetWD1(self):
        return self.wd_base

    def GetWDTrees(self):
        return self.wd2

    def GetSpeciesTreeFN(self):
        return self.speciesTreeRootedIDsFN
            
""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """
""" ************************************************************************************************************************* """

def InitialiseFileHandler(options, fastaDir=None, continuationDir=None, resultsDir_nonDefault=None, pickleDir_nonDefault=None):
    """
    Creates a file handler object which will determine the location of all the files:
    Results will be under the user specified directory of the default results location. Defaults:
        - New, from start: 
                FastaDir/OrthoFinder/Results_Date
            or
                resultsDir_nonDefault/Results_Date
        - New, continuation: Existing_OrthoFinder_Dir/Results_Date
        - Old, continuation: 
                ContinuationDir/OrthoFinder/Results_Date
            or 
                resultsDir_nonDefault/Results_Date
        
    
    Implementation
    1. Working out if an old directory structure is being used
    2. Construct and apporpriate PreviousFilesLocator if necessary - this locates all required files
    3. Pass this to FileHandler - this creates the directory structure required for this run
    4. if error: print and exit
    5. Return FileHandler
    
    Tasks:
    - Switch this round, I can tell if it's and old or new directory right from the start - read log and check info present,
    perhaps just psss it to the new file handler and let it decide if everything is there
    """
    # 1 & 2
    print("Args available")
    print((fastaDir, continuationDir, resultsDir_nonDefault, pickleDir_nonDefault))
    if options.qStartFromFasta and not options.qStartFromBlast:
        pfl = None
        base_dir = resultsDir_nonDefault if resultsDir_nonDefault != None else fastaDir + "OrthoFinder/"
        if not os.path.exists(base_dir): os.mkdir(base_dir)
    else:
        try:
            pfl = PreviousFilesLocator(options, continuationDir)
            # don't create any new directory, it already exists
            base_dir = pfl.GetHomeForResults()
        except Unprocessable:
            print("Using old file locator")
            pfl = PreviousFilesLocator_old(options, continuationDir)
            base_dir = resultsDir_nonDefault if resultsDir_nonDefault != None else pfl.GetHomeForResults()
            if not os.path.exists(base_dir): os.mkdir(base_dir)
        print("\nPrevious file locator identified directories:")
        print((pfl.GetWD1(), pfl.GetHomeForResults()))
        print("\nDir for results: " + base_dir)
    
    # 3 
    # RefactorDS - this might be suitable as a constructor now
    # base_dir - should now exist
    FileHandler.CreateOutputDirectories(options, pfl, base_dir, fastaDir)    
       

    

        