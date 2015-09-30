#background worker to do jobs

import time
import threading

from constants import *
from loggingHelper import *
from jobManager import JobManager
from workerJob import WorkerJob
from rssProcessor import *
from linkProcessor import *
import clusteringJobs as cj
import dbJobs as dj

def RunJob(job):
    "Run a job taking care of error handling."

    try:
        if job.jobName == JOB_PROCESSFEED:
            processFeed(job.jobId, job.jobParams[JOBARG_PROCESSFEED_FEEDID])
        if job.jobName == JOB_PROCESSLINK:
            processLink(job.jobId, job.jobParams[JOBARG_PROCESSLINK_LINKID])
        if job.jobName == JOB_PARSEDOC:
            cj.parseDoc(job.jobId, job.jobParams[JOBARG_PARSEDOC_DOCID])
        if job.jobName == JOB_GETCANDIDATEDOCS:
            cj.getCandidateDocs(
                job.jobId,
                job.jobParams[JOBARG_GETCANDIDATEDOCS_DOCID])
        if job.jobName == JOB_COMPAREDOCS:
            cj.compareDocs(
                job.jobId,
                job.jobParams[JOBARG_COMPAREDOCS_DOC1ID],
                job.jobParams[JOBARG_COMPAREDOCS_DOC2ID])
        if job.jobName == JOB_CLUSTERDOCS:
            cj.clusterDocs(job.jobId)
        if job.jobName == JOB_UPDATEDBTHROUGHPUT:
            dj.updateDbThroughput(
                job.jobId,
                job.jobParams[JOB_UPDATEDBTHROUGHPUT_CONNECTIONSTRING],
                job.jobParams[JOB_UPDATEDBTHROUGHPUT_READTHOUGHPUT],
                job.jobParams[JOB_UPDATEDBTHROUGHPUT_WRITETHOUGHPUT],
                job.jobParams[JOB_UPDATEDBTHROUGHPUT_INDEXNAME])
    except:
        logging.exception('')

def DequeueAndStartJob():
    """
    Dequeue a job from the queue and start executing it.
    """

    logging.info("Dequeing a job.");
    jobManager = JobManager()
    job = jobManager.dequeueJob()

    if job is None:
        logging.info("No job found.")
        return

    logging.info(
        "Job found. Starting it now." + "Job id: %s. Job Name: %s.",
        job.jobId,
        job.jobName)
    RunJob(job)

class JobThread(threading.Thread):
   def __init__ (self):
      threading.Thread.__init__(self)
   def run(self):
      DequeueAndStartJob()

MAX_JOB_THREADS = 15

if __name__ == '__main__':
    InitLogging()
    while (True):
        #subtracting 1 because current parent thread is also counted
        nThreads = threading.activeCount() - 1
        logging.info("No of threads are: %i", nThreads)

        if nThreads < MAX_JOB_THREADS:
            jobThread = JobThread()
            jobThread.start()
        else:
            logging.info("Too many threads. Sleeping")
            time.sleep(5)
