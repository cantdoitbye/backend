from connection.models import Relation,SubRelation

def get_relation_from_subrelation(subrelation):
    try:
        # print(subrelation)
        # Fetch the SubRelation by its ID
        subrelation = SubRelation.objects.get(sub_relation_name__iexact=subrelation)
        
        # Access the related Relation object
        relation = subrelation.relation
        return relation
    except SubRelation.DoesNotExist:
        return None

def get_subrelation(subrelation):
    try:
        # print(subrelation)
        # Fetch the SubRelation by its ID
        subrelation = SubRelation.objects.get(sub_relation_name__iexact=subrelation)
        
        # Access the related Relation object
        relation = subrelation
        return relation
    except SubRelation.DoesNotExist:
        return None
