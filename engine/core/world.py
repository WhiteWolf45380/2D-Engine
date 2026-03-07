# ======================================== IMPORTS ========================================
from .._internal import expect
from .entity import Entity
from .system import System

# ======================================== MONDE ========================================
class World:
    """Gère le monde virtuel et l'organisation des entités"""
    def __init__(self):
        self._all_entities: set = {}     # ensemble des entités
        self._all_systems: set = {}      # ensemble des systèmes
    
    # ======================================== ENTITES ========================================
    def add_entity(self, entity: Entity):
        """
        Ajoute une entité au monde

        Args:
            entity(Entity): entité à ajouter
        """
        self._all_entities.add(expect(entity, Entity))
    
    def discard_entity(self, entity: Entity):
        """
        Supprime une entité du monde

        Args:
            entity(Entity): entité à supprimer
        """
        self._all_entities.discard(entity)
    
    @property
    def entity_count(self) -> int:
        """Retourne le nombre d'entités dans le monde"""
        return len(self._all_entities)
    
    def has_entity(self, entity: Entity) -> bool:
        """Vérifie que le monde comporte une entité donnée"""
        return entity in self._all_entities

    # ======================================== SYSTEMES ========================================
    def add_system(self, system: System):
        """
        Ajoute un système au monde

        Args:
            system(System): système à ajouter
        """
        self._all_systems.add(expect(system, System))
    
    def discard_system(self, system: System):
        """
        Supprime un système du monde

        Args:
            system(System): système à supprimer
        """
        self._all_systems.discard(system)