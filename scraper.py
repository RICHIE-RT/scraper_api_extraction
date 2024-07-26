import os
import time
import requests
from dotenv import load_dotenv
from utils import utility
from datetime import datetime, timedelta
from utils.bk_event import Website, Website2
from utils.log_init import info_logger, error_logger
load_dotenv()

DEVELOPER_TESTING = os.getenv("DEVELOPER_TESTING")


class WebsiteScraper:

    # NOTE: Not implementing the session(requests) because maybe you can switch on proxies or AWS lambda.
    def __init__(self, type_short_name: str, event_id: int) -> None:
        self.name = "example"
        self.id = "123"
        self.event_id = event_id
        self.type_short_name = type_short_name
        self.home_link = "https://www.example.com"
        self.event_api = f"https://www.example.com/Competitions/{self.event_id}?displayType=default"
        self.event_api_headers = {
            "authority": "www.example.com",
            "accept": "application/json",
            "content-type": "application/json",
            "referer": "https://www.example.com",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        }
        self.match_api = "https://www.example.com/Events/[MATCH_ID]/?displayWinnersPriceMkt=true" # MATCH_ID = EVENT_ID
        self.group_api = "https://www.example.com/Events/[MATCH_ID]/[GROUP_ID]"
        
        self.match_data = dict()
        self.meta_data = dict()
        self.all_details = list()

        self.start_time = time.time().__trunc__()
        self.end_time = 0
        self.meta_data["start_time"] = self.start_time

    def start_scraper(self):
        self.get_event_id()
        self.end_scraper()
        info_logger.info("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    def get_event_id(self):
        response = requests.request("GET", self.event_api, headers=self.event_api_headers)
        if response.status_code == 200:
            try:
                events = response.json()["events"] # matches
                for event in events:
                    self.match_id = event["id"]
                    self.get_match_details()
            except Exception as e:
                error_logger.error(f"Failed to convert into json in get match id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code} | {e}")
        else:
            error_logger.error(f"Failed to get match id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code}")
    
    def get_match_details(self):
        url = self.match_api.replace("[MATCH_ID]", str(self.match_id))
        response = requests.request("GET", url, headers=self.event_api_headers)
        if response.status_code == 200:
            try:
                match_datails = response.json()
                names = match_datails["name"]
                self.match_data["match"] = names
                
                kickoff = str(datetime.fromtimestamp(match_datails["startTime"]) + timedelta(hours=0))[:-3]
                self.match_data["time"] = kickoff
                self.match_data["merge"] = f'{names} | {self.name}'
                self.match_data["data"] = {
                    "name": self.name,
                    "id": self.id
                }

                class_name = match_datails["className"].lower().replace(" ", "-")
                compitition_name = match_datails["competitionName"].lower().replace(" ", "-")
                names = names.lower().replace("(", "").replace(")", "").replace(" ", "-")
                event_link_suffix = f'{class_name}/{compitition_name}/{names}--{self.match_id}'
                self.match_data["event_link"] = f'{self.home_link}/{event_link_suffix}'

                adttioanal_details = match_datails["addtioanl"]
                for adttioanal_detail in adttioanal_details:
                    adttioanal_detail_id = adttioanal_detail["id"]
                    self.get_additional_details(adttioanal_detail_id)

                self.insert_details_into_db()
            except Exception as e:
                error_logger.error(f"Failed to convert into json in get match details for event: {self.type_short_name} | event_id: {self.type_short_name} | event {self.event_id} | match_id: {self.match_id}, status_code: {response.status_code} | {e}")
                return None
        else:
            error_logger.error(f"Failed to get match details for event: {self.type_short_name} | event_id: {self.type_short_name} | event {self.event_id} | match_id: {self.match_id}, status_code: {response.status_code}")
            return None

    def get_additional_details(self, details_group_id: int):
        url = self.group_api.replace("[MATCH_ID]", str(self.match_id)).replace("[details_GROUP_ID]", str(details_group_id))
        response = requests.request("GET", url, headers=self.event_api_headers)
        if response.status_code == 200:
            try:
                detail_groups = response.json()
            except Exception as e:
                error_logger.error(f"Failed to convert into json in get details details for event: {self.type_short_name} | event_id: {self.event_id} | match_id: {self.match_id} | group_id: {details_group_id}, status_code: {response.status_code} | {e}")
                return None
        else:
            error_logger.error(f"Failed to get details details for event: {self.type_short_name} | event_id: {self.event_id} | match_id: {self.match_id} | group_id: {details_group_id}, status_code: {response.status_code}")
            return None

        for detail_group in detail_groups:
            name = detail_group["name"]
            detail, sub_selections = dict(), list()
            selections = detail_group["selections"]
            for selection in selections:
                sub_selections.append({
                    "parameter": selection["name"],
                    "parameter2": selection["type"]
                })
            detail.update({f"{name}": sub_selections})
            self.all_details.append(detail)
        
    def insert_details_into_db(self):
        self.match_data.update({
            "details": self.all_details,
        })
        if DEVELOPER_TESTING:
            utility.write_json(file_name=f"{self.name.lower()}_{self.type_short_name}_match", data=self.match_data)
        else:
            if self.type_short_name == "mlb":
                "INSERT DATA INTO DATABASE"
            else:
                "INSERT DATA INTO DATABASE 2"

        info_logger.info(f"Finished scraping for event name: {self.type_short_name} | event_id: {self.event_id} | match_id: {self.match_id} | details found: {len(self.all_details)}")
        self.top_details = dict()
        self.all_details = list()

    def end_scraper(self):
        self.end_time = time.time().__trunc__()
        self.meta_data["stop_time"] = self.end_time
        self.meta_data["duration"] = self.end_time - self.start_time
        if DEVELOPER_TESTING:
            utility.write_json(file_name=f"{self.name.lower()}_{self.type_short_name}_metadata", data=self.meta_data)
        else:
            "INSERT DATA INTO DATABASE"


class WebsiteScraperEndpoint(WebsiteScraper):

    def __init__(self, type_short_name: str, event_id: int) -> None:
        super().__init__(type_short_name, event_id)
        self.event_api = f"https://www.example.com/{self.event_id}/?displayType=default"
        self.competition_api = f"https://www.example.com/Competitions/[COMPETITIONS_ID]/Events?displayType=default"

    def get_event_id(self):
        response = requests.request("GET", self.event_api, headers=self.event_api_headers)
        if response.status_code == 200:
            try:
                competitions = response.json()
                for competition in competitions:
                    self.competition_id = competition["id"]
                    self.get_competition_details()
            except Exception as e:
                error_logger.error(f"Failed to convert into json in get competition id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code} | {e}")
        else:
            error_logger.error(f"Failed to get competition id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code}")

    def get_competition_details(self):
        url = self.competition_api.replace("[COMPETITIONS_ID]", str(self.competition_id))
        response = requests.request("GET", url, headers=self.event_api_headers)
        if response.status_code == 200:
            try:
                events = response.json() # matches
                for event in events:
                    self.match_id = event["id"]
                    self.get_match_details()
            except Exception as e:
                error_logger.error(f"Failed to convert into json in get event compitition-match id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code} | {e}")
        else:
            error_logger.error(f"Failed to get event compitition-match id for event: {self.type_short_name} | event_id: {self.event_id}, status_code: {response.status_code}")
    

Website_scraper_instance = WebsiteScraper(short_name=Website.TYPE, id=Website.TYPE_ID)
Website_scraper_instance.start_scraper()

Website_scraper_instance2 = WebsiteScraperEndpoint(short_name=Website.TYPE, id=Website.TYPE)
Website_scraper_instance2.start_scraper()
