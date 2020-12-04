import asyncio
import logging
from vrcpy.errors import ObjectErrors

class BaseObject:
    def __init__(self, client, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.client = client

        # "name": {"dict_key": "id", "type": str}
        self.required = {}
        self.optional = {}

    def _get_proper_obj(self, obj, t):
        if type(obj) is not t:
            if t is not dict and t is not list:
                    return t(obj)

        return obj

    def _assign(self, obj):
        logging.debug("Created %s object" % self.__class__.__name__)

        self._object_integrety(obj)
        self.raw = obj

        for key in self.required:
            myobj = self._get_proper_obj(
                obj[self.required[key]["dict_key"]],
                self.required[key]["type"]
            )

            setattr(
                self,
                key,
                myobj
            )

        for key in self.optional:
            if self.optional[key]["dict_key"] in obj:
                setattr(
                    self,
                    key,
                    self._get_proper_obj(
                        obj[self.optional[key]["dict_key"]],
                        self.optional[key]["type"]
                    )
                )
            else:
                setattr(self, key, None)

        if hasattr(self, "__cinit__"):
            self.caching_finished = False
            self.cache_task = self.loop.create_task(self.__cinit__())

        # Save yo memory fool
        del self.required
        del self.optional

    def _object_integrety(self, obj):
        for key in self.required:
            if self.required[key]["dict_key"] not in obj:
                print(obj.keys())
                raise ObjectErrors.IntegretyError(
                    "{} object missing required key {}".format(
                        self.__class__.__name__, self.required[key]["dict_key"]
                    )
                )

    async def wait_for_cache(self):
        '''
        Waits for any caching an object has to do
        '''

        if hasattr(self, "cache_task"):
            while not self.caching_finished:
                await asyncio.sleep(0.1)
