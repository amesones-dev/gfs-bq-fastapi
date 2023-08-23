import base64
import datetime
import logging


class BigQueryContent:

    def __init__(self, *args, **kwargs):
        self.data = None
        self.last_run = None
        self.title = None
        self.sql_query = None

        if 'sql_query' in kwargs:
            self.sql_query = kwargs.get('sql_query')

        if 'title' in kwargs:
            self.title = kwargs.get('title')


def singleton(cls):
    obj = cls()
    # Always return the same object
    cls.__new__ = staticmethod(lambda cls: obj)
    # Disable __init__
    try:
        del cls.__init__
    except AttributeError:
        pass
    return cls


@singleton
class AppBQContentManager:
    # Big Query Connection manager
    bq = None

    def __init__(self, *args, **kwargs):
        self.app = None
        self.app_id = None
        self.titles = None
        self.sql_queries = None
        self.load_titles()
        self.load_sql_queries()

        # content: In memory BiqQueryContent objects dictionary
        self.contents = {}

    def init_app(self, app, bq):
        self.app = app
        self.app_id = app.config.get('VIEW_APP_NAME')
        self.__class__.bq = bq

    def bq_run(self, sql_query):
        # Only run in BQ  if not run already today or empty data
        bq = self.__class__.bq
        data = None
        if sql_query is not None and bq.initialized():
            try:
                query_job = self.bq.client.query(query=sql_query)
                # Wait for job with default timeout and retry policy
                while query_job.done() is False:
                    pass
                # Format job results
                # Result is a group of rows
                output = []
                for row in query_job.result():
                    # Row values can be accessed by field name or index.
                    output.append(row)
                data = [dict(row) for row in output]
            except Exception as e:
                logging.log(level=logging.ERROR, msg="Exception {}:{} Method: {}".format(e.__class__, e,
                                                                                         self.bq_run.__name__))
                data = None
        return data

    def load_content(self, key, *args, **kwargs):
        content_manager = self
        content_key = key

        # Title and query provided by Content Manager
        title = content_manager.titles.get(key)
        sql_query = content_manager.sql_queries.get(key)

        if 'country' in kwargs:
            country = kwargs.get('country')
            if country is not None:
                sql_query = sql_query.replace('<country>', country)
                # Key includes method name and country
                content_key = content_key + '@' + country.lower()
        if 'country_list' in kwargs:
            country_list = kwargs.get('country_list')
            if country_list is not None:
                inline_country_list = country_list.__str__().strip('[').strip(']')
                sql_query = sql_query.replace('<country_list>', inline_country_list)
                # Key includes method name and country
                content_key = content_key + '@' + inline_country_list.lower()
        if 'start_date' in kwargs:
            # Validate start-date format
            start_date = kwargs.get('start_date')
            if start_date is not None:
                sql_query = sql_query.replace('<start_date>', start_date)
                # Key includes method name, country and date
                content_key = content_key + '@' + start_date

        # See if a local BigQueryContent exists in local content_manager
        local_content = content_manager.contents.get(content_key)
        if local_content is None:
            # Create object in local runner memory
            local_content = BigQueryContent(sql_query=sql_query, title=title)
            # Effectively run BiqQuery call with SQL query
            local_content.data = self.bq_run(sql_query=sql_query)
            local_content.last_run = datetime.date.today()
            # Register local_content  in content_manager
            content_manager.contents.update({content_key: local_content})
        else:
            # Already in local runner memory
            # Here check freshness and see whether it needs re-running
            if isinstance(local_content, BigQueryContent):
                if local_content.last_run != datetime.date.today() or local_content.data is None:
                    # bq_run could return None in case of BQ error
                    new_data = self.bq_run(sql_query=sql_query)
                    if new_data is not None:
                        local_content.data = new_data
                        local_content.last_run = datetime.date.today()
        payload = local_content.data
        return payload

    def load_titles(self):
        titles = {}
        titles.update({"get_countries_ranking": "Top 5 countries by total cases"})
        titles.update({"get_countries": "List of countries"})
        titles.update({"get_country_latest_date": "Latest date available"})
        titles.update({"get_country_latest_date_total_confirmed": "Latest cases"})
        titles.update({"get_country_latest_date_total_dead": "Latest dead"})
        titles.update({"get_country_territories": "Territories in country"})
        titles.update({"get_country_latest_date_total": "Latest  cases and dead"})
        titles.update({"get_country_latest_date_total_by_territory": "Latest cases and dead"})
        titles.update({"get_country_summary": "Country summary"})
        titles.update({"get_country_evolution": "Country evolution"})
        titles.update({"get_country_list_summary": "Country list summary"})
        self.titles = titles

    def load_sql_queries(self):
        sql_queries = {}
        sql_queries.update({"get_countries_ranking": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            )
        SELECT country_region,  CAST(MAX(date) AS STRING)  as latest, SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead, 100*SAFE_DIVIDE(SUM(deaths),SUM(confirmed)) as drate
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE date=latest_date_published
        GROUP BY country_region
        ORDER BY total_confirmed DESC, total_dead DESC
        LIMIT 5"""})
        sql_queries.update({"get_country_summary": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            WHERE country_region='<country>'
            )
        SELECT country_region, CAST(MAX(date) AS STRING) as latest, SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead,  100*SAFE_DIVIDE(SUM(deaths),SUM(confirmed)) as drate
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE country_region='<country>' AND date=latest_date_published
        GROUP BY country_region"""})
        sql_queries.update({"get_country_evolution": """
               WITH 
               available  AS
                       (
                       SELECT  MAX(date) as latest_date_published, date_sub(MAX(date),INTERVAL 1 MONTH) as month_before, date_sub(MAX(date),INTERVAL 2 MONTH) as month_2_before
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
                       WHERE country_region='<country>'
                       ),
               latest_data AS
                      (
                       SELECT country_region, date, SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=latest_date_published
                       GROUP BY date, country_region
                      ),
               month_before_data AS
                      (
                       SELECT date, SUM(confirmed) as mb_total_confirmed, SUM(deaths)  as mb_total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=month_before
                       GROUP BY date, country_region
                      ),
               month_2_before_data AS
                      (
                       SELECT date, SUM(confirmed) as m2b_total_confirmed, SUM(deaths)  as m2b_total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=month_2_before
                       GROUP BY date, country_region
                      ),
               stats AS 
                     (
                        SELECT 100*SAFE_DIVIDE(total_dead, total_confirmed) as drate,100*SAFE_DIVIDE(mb_total_dead,mb_total_confirmed) as mb_drate, 100*SAFE_DIVIDE(m2b_total_dead,m2b_total_confirmed) as m2b_drate,
                        total_confirmed-mb_total_confirmed as inc_m_confirmed, 
                        total_dead-mb_total_dead as inc_m_dead, 
                        mb_total_confirmed-m2b_total_confirmed as inc_m2_confirmed,
                        mb_total_dead-m2b_total_dead as inc_m2_dead,
                        FROM latest_data, month_before_data, month_2_before_data
                     ),
               change_stats AS 
                     (
                       SELECT SAFE_DIVIDE(inc_m_confirmed - inc_m2_confirmed, inc_m_confirmed+inc_m2_confirmed) as rate_inc_c_m2,
                       SAFE_DIVIDE(inc_m_dead - inc_m2_dead ,inc_m_dead + inc_m2_dead) as rate_inc_d_m2
                       FROM stats
                     )

               SELECT country_region, CAST (latest_date_published AS STRING) as latest_date, total_confirmed, total_dead, drate,  inc_m_confirmed, inc_m_dead, rate_inc_c_m2, rate_inc_d_m2

               FROM available, latest_data, month_before_data, month_2_before_data, stats, change_stats

           """})
        sql_queries.update({"get_countries": """SELECT DISTINCT country_region 
                FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`
                WHERE DATE_DIFF(CURRENT_DATE(), date, YEAR)<1
                 ORDER BY country_region ASC"""})
        sql_queries.update({"get_country_latest_date": """SELECT CAST (MAX(date) AS STRING)  as latest_date
                FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
                WHERE country_region='<country>'"""})
        sql_queries.update({"get_country_latest_date_total_confirmed": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            WHERE country_region='<country>'
            )
        SELECT CAST(MAX(date) AS STRING) as latest, SUM(confirmed)  as total_confirmed
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE country_region='<country>' AND date=latest_date_published"""})
        sql_queries.update({"get_country_latest_date_total_dead": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            WHERE country_region='<country>'
            )
        SELECT CAST(MAX(date) AS STRING) as latest, SUM(deaths)  as total_dead
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE country_region='<country>' AND date=latest_date_published"""})
        sql_queries.update({"get_country_latest_date_total": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            WHERE country_region='<country>'
            )
        SELECT CAST(MAX(date) as latest_date AS STRING), SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE country_region='<country>' AND date=latest_date_published
        GROUP BY country_region"""})
        sql_queries.update({"get_country_latest_date_total_by_territory": """WITH available  AS
            (
            SELECT MAX(date) as latest_date_published
            FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
            WHERE country_region='<country>'
            )
        SELECT province_state as territory, CAST(MAX(date) AS STRING) as latest, SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
        WHERE country_region='<country>' AND date=latest_date_published
        GROUP BY territory
        ORDER BY territory"""})
        sql_queries.update({"get_country_territories": """SELECT DISTINCT(province_state)  as territory
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`
        WHERE country_region='<country>' AND province_state  is  not NULL"""})
        sql_queries.update({"get_country_closest_date": """SELECT CAST(MAX(date) AS STRING)  as closest_available_date
                FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
                WHERE country_region='<country>' AND DATE_DIFF(DATE(DATETIME "<input-date>"), date, DAY)>=0"""})
        sql_queries.update({"get_country_closest_date_total": """
                WITH closest AS
                (SELECT MAX(date)  as published_date
                        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
                        WHERE country_region='<country>' AND DATE_DIFF(DATE(DATETIME "<start_date>"), date, DAY)>=0
                ),                
               available  AS
                       (
                       SELECT  published_date as latest_date_published, date_sub(MAX(date),INTERVAL 1 MONTH) as month_before, date_sub(MAX(date),INTERVAL 2 MONTH) as month_2_before
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`, closest
                       WHERE country_region='<country>'
                        GROUP BY latest_date_published
                       ),
               latest_data AS
                      (
                       SELECT country_region, date, SUM(confirmed) as total_confirmed, SUM(deaths)  as total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=latest_date_published
                       GROUP BY date, country_region
                      ),
               month_before_data AS
                      (
                       SELECT date, SUM(confirmed) as mb_total_confirmed, SUM(deaths)  as mb_total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=month_before
                       GROUP BY date, country_region
                      ),
               month_2_before_data AS
                      (
                       SELECT date, SUM(confirmed) as m2b_total_confirmed, SUM(deaths)  as m2b_total_dead
                       FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`,  available
                       WHERE country_region='<country>' AND date=month_2_before
                       GROUP BY date, country_region
                      ),
               stats AS 
                     (
                        SELECT 100*SAFE_DIVIDE(total_dead, total_confirmed) as drate,100*SAFE_DIVIDE(mb_total_dead,mb_total_confirmed) as mb_drate, 100*SAFE_DIVIDE(m2b_total_dead,m2b_total_confirmed) as m2b_drate,
                        total_confirmed-mb_total_confirmed as inc_m_confirmed, 
                        total_dead-mb_total_dead as inc_m_dead, 
                        mb_total_confirmed-m2b_total_confirmed as inc_m2_confirmed,
                        mb_total_dead-m2b_total_dead as inc_m2_dead,
                        FROM latest_data, month_before_data, month_2_before_data
                     ),
               change_stats AS 
                     (
                       SELECT SAFE_DIVIDE(inc_m_confirmed - inc_m2_confirmed, inc_m_confirmed+inc_m2_confirmed) as rate_inc_c_m2,
                       SAFE_DIVIDE(inc_m_dead - inc_m2_dead ,inc_m_dead + inc_m2_dead) as rate_inc_d_m2
                       FROM stats
                     )

               SELECT country_region, CAST (latest_date_published AS STRING) as latest_date, total_confirmed, total_dead, drate,  inc_m_confirmed, inc_m_dead, rate_inc_c_m2, rate_inc_d_m2

               FROM available, latest_data, month_before_data, month_2_before_data, stats, change_stats
        """})
        sql_queries.update({"get_country_closest_date_total_by_territory": """
        WITH closest AS
        (SELECT MAX(date)  as published_date
                FROM `bigquery-public-data.covid19_jhu_csse_eu.summary` 
                WHERE country_region='<country>' AND DATE_DIFF(DATE(DATETIME "<start_date>"), date, DAY)>=0
        )
        SELECT CAST(closest.published_date AS STRING) as latest_date, province_state as territory, SUM(confirmed) as total_confirmed, SUM(deaths) as total_dead, 100*SAFE_DIVIDE(SUM(deaths),SUM(confirmed)) as drate
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`, closest
        WHERE country_region='<country>' and date=closest.published_date
        GROUP BY  closest.published_date, territory
        ORDER BY closest.published_date DESC, territory ASC
        """})
        sql_queries.update({"get_country_list_summary": """
        WITH published AS
        (
        SELECT  MAX(date) as latest, country_region as country
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`
        WHERE country_region in (<country_list>)
        GROUP BY country_region
        )

        SELECT CAST(latest AS STRING), country, SUM(confirmed) as total_confirmed, SUM(deaths) as total_dead
        FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`, published
        WHERE date=latest and country_region=country
        GROUP BY country, latest
        """})
        self.sql_queries = sql_queries
