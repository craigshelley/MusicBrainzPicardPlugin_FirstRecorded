# -*- coding: utf-8 -*-
# Copyright 2017 Craig Shelley
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

PLUGIN_NAME = "First Recorded"
PLUGIN_AUTHOR = u"Craig Shelley"
PLUGIN_DESCRIPTION = "Fetch the date of the first known recording.   e.g.: " + '$set(date,$if2(%firstrecorded%,%originaldate%,%date%))'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9", "0.10", "0.11", "0.15"]

from picard import log
from picard.metadata import (
    register_track_metadata_processor,
    register_album_metadata_processor,
    )

from datetime import datetime



class MyLookup():
    def __init__(self, album, metadata, track_node, release_node):
        self.album=album
        self.metadata=metadata
        self.track_node=track_node
        self.release_node=release_node

    def myhandler(self, document, http, error):
        self.album._requests-=1

        if error:
            if "Temporarily Unavailable" in http.errorString() :
                log.info("HTTP Temporarily Unavailable - Repeating lookup later")
                self.mydolookup()
            else:
                self.album._finalize_loading(True)
            return

        log.debug("Track = %s (%s)", self.track_node.recording[0].id, self.track_node.recording[0].title[0].text)
        olddate = datetime.now()
        newdate = datetime(1,1,1,0,0,0)
        for release in document.metadata[0].recording[0].release_list[0].release:

            try:
                log.debug("\tDate=%s", release.date[0].text)

                if len(release.date[0].text) == 10:
                    dtstrmin=dtstrmax=release.date[0].text
                elif len(release.date[0].text) == 4:
                    dtstrmin=release.date[0].text + "-01-01"
                    dtstrmax=release.date[0].text + "-12-31"
                else:
                    continue
            except:
                continue
            
            try:
                dtobjmin=datetime.strptime(dtstrmin, '%Y-%m-%d')
                dtobjmax=datetime.strptime(dtstrmax, '%Y-%m-%d')
            except:
                log.info("ERROR: Unknown date format dtstrmin='%s' dtstrmax='%s' for Recording ID: %s", dtstrmin, dtstrmax, self.track_node.recording[0].id)
                continue

            if dtobjmax < olddate:
                olddate=dtobjmax
                olddatestr=release.date[0].text

            if dtobjmin > newdate:
                newdate=dtobjmin
                newdatestr=release.date[0].text

        try:
            self.metadata['firstrecorded']=olddatestr
            log.debug ("Oldest Date = %s", olddatestr)
        except:
            log.info ("Unable to find oldest date for Recording ID: %s", self.track_node.recording[0].id)
        finally:
            self.album._finalize_loading(None)


    def mydolookup(self):
        self.album._requests+=1
        self.album.tagger.xmlws._get_by_id('recording', self.track_node.recording[0].id, self.myhandler, ['releases']);



def first_year_track(album, metadata, track_node, release_node):
    mylookup=MyLookup(album, metadata,track_node, release_node)   
    mylookup.mydolookup()

register_track_metadata_processor(first_year_track)
