from app.models import Highlightable

class Selector():
    items: set[Highlightable] = set()
    
    def select(self, item):
        self.clear()
        self.add(item)
        
    def add(self, item: Highlightable):
        self.items.add(item)
        item.highlight()
    
    def remove(self, item: Highlightable):
        self.items.remove(item)
        item.remove_highlight()

    def clear(self):
        for item in self.items:
            item.remove_highlight()
        self.items.clear()
    
