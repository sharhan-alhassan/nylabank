from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from sqlalchemy import func, and_, desc, asc
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import RelationshipProperty
from ..db.base_class import Base

# Generics for typing
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    A base CRUD class for SQLAlchemy with functionality similar to Django ORM.
    Provides common CRUD operations and advanced query capabilities.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUD class with the model.
        :param model: The SQLAlchemy model class
        """
        self.model = model

    async def get(
        self,
        db: AsyncSession,
        id: Any,
        joins: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
    ) -> Optional[ModelType]:
        """
        Retrieve a single object by ID, with optional relationship loading and specific fields.

        Args:
            db (AsyncSession): Database session for executing the query.
            id (Any): The ID of the object to retrieve.
            joins (Optional[List[Any]]): List of relationships to load using joinedload.
            fields (Optional[List[Any]]): Specific fields to select (default is all fields).

        Returns:
            Optional[ModelType]: The retrieved object or None if not found.
        """
        # If fields are specified, we can't use joinedload
        if fields:
            query = select(*fields)
            query = query.filter(self.model.id == id)
        else:
            query = select(self.model)
            query = query.filter(self.model.id == id)
            # Apply joins for eager loading of relationships
            if joins:
                for join in joins:
                    query = query.options(joinedload(join))

        result = await db.execute(query)
        return result.scalars().first()

    async def get_by(
        self,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        joins: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
    ) -> Optional[ModelType]:
        """
        Retrieve a single object by specified filters, optional joins, and specific fields.

        Args:
            db (AsyncSession): Database session.
            filters (Optional[Dict[str, Any]]): Dictionary of field-value pairs to filter by.
            joins (Optional[List[Any]]): Relationships to eagerly load using joinedload.
            fields (Optional[List[Any]]): Specific fields to select (default is all fields).

        Returns:
            Optional[ModelType]: The retrieved object or None if no match is found.
        """
        query = select(*fields) if fields else select(self.model)

        # Apply filters if provided
        if filters:
            query = query.filter_by(**filters)

        # Apply joins for eager loading of relationships
        if joins:
            for join in joins:
                query = query.options(joinedload(join))

        result = await db.execute(query)
        return result.scalars().first()

    async def filter(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None,
        joins: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = 10,
        skip: Optional[int] = 0,
    ) -> Dict[str, Any]:
        """
        Filter items with optional conditions, joins, fields, ordering, and pagination.
        """
        # Enforce maximum limit
        if limit > 20:
            limit = 20

        # Start query with specific fields or the full model
        query = select(*fields) if fields else select(self.model)

        # Apply filters
        if filters:
            conditions = self._build_filter_conditions(filters)
            query = query.filter(and_(*conditions))

        # Apply joins for eager loading of relationships
        if joins:
            for join in joins:
                query = query.options(joinedload(join))

        # Apply ordering
        if order_by:
            order_conditions = []
            for col in order_by:
                if col.startswith("-"):  # Descending order
                    order_conditions.append(desc(getattr(self.model, col[1:])))
                else:  # Ascending order
                    order_conditions.append(asc(getattr(self.model, col)))
            query = query.order_by(*order_conditions)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query and fetch results
        result = await db.execute(query)
        items = result.scalars().all()

        # Get total count
        total_query = select(func.count()).select_from(self.model)
        if filters:
            total_query = total_query.filter(and_(*conditions))
        total = await db.execute(total_query)
        total_count = total.scalar()

        return {
            "message": "Filtered data retrieved successfully.",
            "total_count": total_count,
            "data": items,
        }

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> List[Any]:
        conditions = []
        for key, value in filters.items():
            if "__" in key:
                parts = key.split("__")
                field_name = parts[0]
                operator = parts[1] if len(parts) > 1 else None

                if not hasattr(self.model, field_name):
                    continue  # Skip if field doesn't exist

                field = getattr(self.model, field_name)

                if operator == "gte":
                    conditions.append(field >= value)
                elif operator == "lte":
                    conditions.append(field <= value)
                elif operator == "gt":
                    conditions.append(field > value)
                elif operator == "lt":
                    conditions.append(field < value)
                elif operator == "ne":
                    conditions.append(field != value)
                elif operator == "in":
                    conditions.append(field.in_(value))
                elif operator == "not_in":
                    conditions.append(~field.in_(value))
                elif operator == "like":
                    conditions.append(field.like(f"%{value}%"))
                elif operator == "ilike":
                    conditions.append(field.ilike(f"%{value}%"))
                else:
                    # Handle nested relationships (original logic)
                    attr = field
                    for part in parts[1:]:
                        if hasattr(attr, "property") and hasattr(
                            attr.property, "mapper"
                        ):
                            attr = getattr(attr.property.mapper.class_, part)
                        else:
                            attr = getattr(attr, part)
                    conditions.append(attr == value)
            else:
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
        return conditions

    async def all(
        self,
        db: AsyncSession,
        *,
        joins: Optional[List[Any]] = None,
        fields: Optional[List[Any]] = None,
        limit: Optional[int] = 50,
        skip: Optional[int] = 0,
    ) -> Dict[str, Any]:
        """
        Fetch all items with optional joins, specific fields, and pagination.
        """
        # Enforce maximum limit
        if limit > 100:
            limit = 100

        # Start query with specific fields or the full model
        query = select(*fields) if fields else select(self.model)

        # Apply joins for eager loading of relationships
        if joins:
            for join in joins:
                query = query.options(joinedload(join))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query and fetch results
        result = await db.execute(query)
        items = result.scalars().unique().all()

        # Get total count
        total_query = select(func.count()).select_from(self.model)
        total = await db.execute(total_query)
        total_count = total.scalar()

        return {
            "detail": "All data retrieved successfully.",
            "total_count": total_count,
            "data": items,
        }

    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelType:
        """
        Retrieve a single object by ID or raise 404 if not found.
        """
        obj = await self.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with ID {id} not found",
            )
        return obj

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        refresh_relationships: Optional[List[Any]] = None,
    ) -> ModelType:
        """
        Create a new object.

        Args:
            db (AsyncSession): Database session
            obj_in (CreateSchemaType): Data to create object with
            refresh_relationships (Optional[List[str]]): List of relationship names to refresh after creation
        """
        try:
            obj_in_data = (
                obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
            )
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            await db.commit()

            if refresh_relationships:
                relationship_names = [rel.key for rel in refresh_relationships]
                await db.refresh(db_obj, relationship_names)
            else:
                await db.refresh(db_obj)

            return db_obj
        except Exception as e:
            await db.rollback()
            raise e

    async def create_related_objects(
        self,
        db: AsyncSession,
        parent_obj: ModelType,
        relationship_name: str,
        related_data: List[Dict[str, Any]],
        related_crud: "BaseCRUD",
        related_create_schema: Type[BaseModel],
        filter_field: str,
    ) -> None:
        """
        Handle the creation and association of related objects.
        """
        if not related_data:
            return

        relationship = getattr(self.model, relationship_name, None)
        if not relationship or not isinstance(
            relationship.property, RelationshipProperty
        ):
            raise ValueError(f"Invalid relationship: {relationship_name}")

        try:
            related_objects = []
            for data in related_data:
                filter_value = (
                    data[filter_field]
                    if isinstance(data, dict)
                    else getattr(data, filter_field)
                )

                # Check if the related object already exists
                existing_obj = await related_crud.get_by(
                    db, filters={filter_field: filter_value}
                )

                if not existing_obj:
                    # Create new object if it doesn't exist
                    create_data = data if isinstance(data, dict) else data.model_dump()
                    # Handle foreign key relationships properly
                    if hasattr(create_data, "parent_id"):
                        create_data["parent_id"] = parent_obj.id
                    schema_instance = related_create_schema(**create_data)
                    existing_obj = await related_crud.create(db, obj_in=schema_instance)

                related_objects.append(existing_obj)

            # Handle different relationship types
            relationship_collection = getattr(parent_obj, relationship_name)
            if hasattr(relationship_collection, "extend"):
                relationship_collection.extend(related_objects)
            elif hasattr(relationship_collection, "update"):
                relationship_collection.update(related_objects)
            else:
                # For one-to-many or one-to-one
                for obj in related_objects:
                    if obj not in relationship_collection:
                        relationship_collection.append(obj)

            db.add(parent_obj)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing related objects: {str(e)}",
            )

    async def create_many(
        self, db: AsyncSession, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """
        Create multiple objects in one transaction.
        """
        db_objs = [self.model(**obj.dict()) for obj in objs_in]
        db.add_all(db_objs)
        await db.commit()
        return db_objs

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update an existing object.
        """
        obj_data = jsonable_encoder(db_obj)
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_many(self, db: AsyncSession, objs: List[ModelType]) -> None:
        """
        Update multiple objects in one transaction.
        """
        for obj in objs:
            db.add(obj)
        await db.commit()

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Delete an object by ID.
        """
        obj = await self.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with ID {id} not found",
            )
        await db.delete(obj)
        await db.commit()
        return obj

    async def delete_many(self, db: AsyncSession, ids: List[Any]) -> None:
        """
        Delete multiple objects by IDs.
        """
        query = select(self.model).filter(self.model.id.in_(ids))
        result = await db.execute(query)
        objs = result.scalars().all()
        for obj in objs:
            await db.delete(obj)
        await db.commit()

    async def count(
        self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count the total number of objects.
        """
        query = select(func.count()).select_from(self.model)
        if filters:
            conditions = self._build_filter_conditions(filters)
            if conditions:  # Only apply filter if there are valid conditions
                query = query.filter(and_(*conditions))
        result = await db.execute(query)
        return result.scalar()

    async def exists(self, db: AsyncSession, **kwargs) -> bool:
        """
        Check if an object exists with the given conditions.
        """
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        return result.scalar() is not None

    # --- Aggregation Methods ---
    async def aggregate(self, db: AsyncSession, field: str, func_name: str) -> Any:
        """
        Perform aggregation on a field (e.g., sum, avg, max, min).
        """
        agg_func = getattr(func, func_name, None)
        if not agg_func:
            raise ValueError(f"Invalid aggregation function: {func_name}")
        query = select(agg_func(getattr(self.model, field)))
        result = await db.execute(query)
        return result.scalar()

    # --- Utility Methods ---
    async def get_related(
        self, db: AsyncSession, id: Any, relationship: str
    ) -> List[Any]:
        """
        Get related objects for a relationship field.
        """
        obj = await self.get(db, id)
        if not obj or not hasattr(obj, relationship):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related field {relationship} not found on {self.model.__name__}",
            )
        return getattr(obj, relationship)

    async def add_to_relationship(
        self,
        db: AsyncSession,
        *,
        obj_id: Any,
        relationship_name: str,
        related_obj: Any,
    ) -> ModelType:
        """
        Add a related object to a relationship collection.

        Example:
            # Add a tag to a comment
            await comment_crud.add_to_relationship(
                db,
                obj_id=comment_id,
                relationship_name="tags",
                related_obj=tag
            )
        """
        parent_obj = await self.get(db, obj_id)
        if not parent_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found",
            )

        relationship = getattr(parent_obj, relationship_name, None)
        if not relationship:
            raise ValueError(f"Relationship {relationship_name} not found")

        # Handle different relationship types
        if hasattr(relationship, "append"):
            if related_obj not in relationship:
                relationship.append(related_obj)
        elif hasattr(relationship, "add"):
            relationship.add(related_obj)
        else:
            # For one-to-one relationships
            setattr(parent_obj, relationship_name, related_obj)

        db.add(parent_obj)
        await db.commit()
        await db.refresh(parent_obj)
        return parent_obj
