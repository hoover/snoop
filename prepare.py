import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

engine = sa.create_engine('postgresql:///maldini')
Base = declarative_base()

class Document(Base):
    __tablename__ = 'document'
    id = sa.Column(sa.Text, primary_key=True)
    path = sa.Column(sa.Text)

def main():
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    main()
