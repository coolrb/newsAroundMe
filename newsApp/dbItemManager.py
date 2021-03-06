#TODO: make separate class for exceptions and raise them instead of generic
import decimal

from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
from retrying import retry

from dbItem import DbItem
from dbhelper import *

class DbItemManager:
    """
    Manage DbItems stored on AWS dynamo db database.

    Contains functions for CRUD operations on the DbItems stored
    """

    def __init__(self, tableConnString):
        """
        Instantiates a new instance of DbItemManager class

        'TableConnString' : connection string of the table.
        """

        self.tableConnString = tableConnString;

        tagsTableConnectionParams = parseConnectionString(
            self.tableConnString);
        self.table = Table(
            tagsTableConnectionParams['name'],
            schema = [HashKey('itemId'), RangeKey('tagName')],
            connection = getDbConnection(tagsTableConnectionParams))

    def __getTables(self):
        """
        Get the tables.
        """

        return self.table

    def __getTagsFromTagsTableRows(self, tagsTableRows):
        """
        Convert data retrieved from tagsTable to a dictionary
        """

        tags = {}

        for tag in tagsTableRows:
            tags[tag['tagName']] = tag['tagValue']

            # boto retrieves numbers as decimals. Convert them to float
            # else we'll have json serialization issues down the pipeline
            if type(tag['tagValue']) is decimal.Decimal:
                tags[tag['tagName']] = float(tag['tagValue'])

        return tags

    def __getItemTags(self, tagsTable, itemId):
        """
        Get tags as a dictionary given tagsTable and db item Id
        """

        tagsTableRows = tagsTable.query_2(
            itemId__eq = itemId,
            max_page_size=25);
        return self.__getTagsFromTagsTableRows(tagsTableRows)

    @retry(stop_max_attempt_number=3)
    def put(self, item):
        """
        Put a new item.
        """

        tagsTable = self.__getTables()

        with tagsTable.batch_write() as batch:
            for tagName in item.tags:
                batch.put_item(data = {
                    'itemId' : item.id,
                    'tagName' : tagName,
                    'tagValue' : item.tags[tagName]},
                overwrite = True)

    def get(self, itemId):
        """
        Get item with the specified Id.
        """

        tagsTable = self.__getTables()

        itemTags = self.__getItemTags(tagsTable, itemId)
        if not itemTags:
            raise Exception("dbItem not found")

        return DbItem(itemId, itemTags)

    def getEntriesWithTag(self, tagName):
        """
        Get all entries with specified tagName.
        """

        tagsTable = self.__getTables()
        return tagsTable.query_2(
            tagName__eq = tagName,
            index = 'tagName-itemId-index');

    def delete(self, itemId):
        """
        Delete item with the specified Id from the databases.
        """

        tagsTable = self.__getTables()

        itemTags = self.__getItemTags(tagsTable, itemId)

        with tagsTable.batch_write() as batch:
            for itemTagName in itemTags:
                batch.delete_item(
                    itemId=itemId,
                    tagName=itemTagName)

        return
