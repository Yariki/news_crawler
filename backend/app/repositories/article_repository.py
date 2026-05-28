



from sqlalchemy import select

from app.models.article import Article


class ArticleRepository:
    """ Repository class responsible for managing Article records in the database. It provides methods to add new articles, update existing articles, and retrieve article information based on ID. This class abstracts away the database interactions related to the Article model, allowing other parts of the application to work with Article objects without needing to know about the underlying database structure."""
    
    def __init__(self, db):
        self.db = db

    async def add_article(self, new_article: Article) -> Article:
        """Adds a new article record to the database based on the provided Article object."""
        self.db.add(new_article)
        await self.db.commit()
        return new_article
    
    async def get_article_by_id(self, article_id):
        """Retrieves an article record from the database based on the provided article ID. If a record is found, it returns the Article object; otherwise, it returns None."""
        query  = (
            select(Article).where(Article.id == article_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_articles_urls(self, urls: list[str]) -> list[str]:
        """Retrieves article URLs from the database that match the provided list of URLs. It returns a list of URLs that are found in the database."""
        query = (
            select(Article.url).where(Article.url.in_(urls))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_articles(self, limit=20):
        """Retrieves recent article records from the database, ordered by published date in descending order. The number of articles returned can be limited by providing a value for the limit parameter."""
        query = (
            select(Article).order_by(Article.published_at.desc()).limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_article(self, article_id, updated_article: Article):
        """Updates an existing article record in the database with new data from the provided Article object. The article to be updated is identified by the article_id parameter. If the article is found and updated successfully, it returns the updated Article object; otherwise, it returns None."""
        existing_article = await self.get_article_by_id(article_id)
        if not existing_article:
            return None
        
        for key, value in updated_article.__dict__.items():
            if key != "id" and value is not None:
                setattr(existing_article, key, value)
        
        await self.db.commit()
        return existing_article
