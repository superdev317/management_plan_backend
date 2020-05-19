from rest_framework import serializers
from .models import Bid, Ask
from projects.serializers import MoneyField
from projects.models import UserCompanyShares, Project


class BidSerializer(serializers.ModelSerializer):
    """
    Serializer for Bid
    """
    price = MoneyField(required=False, allow_null=True,)
    limit_price = MoneyField(required=False, allow_null=True,)
    
    class Meta:
        model = Bid

        fields = ('id','exchange_type','order_time','project','quantity','price','order_type','limit_price','bid_by')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('quantity') and attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity.') 
        elif not attrs.get('quantity') and not attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity and company.')  
        elif not attrs.get('quantity') and attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity and exchange type.') 
        elif attrs.get('quantity') and not attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set project.')
        elif attrs.get('quantity') and not attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set project and exchange type.')
        elif attrs.get('quantity') and attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set exchange type.')
        elif attrs.get('order_type') == 'limit' and not attrs.get('limit_price'):
            raise serializers.ValidationError('Please set limit price.')
        return attrs


class AskSerializer(serializers.ModelSerializer):
    """
    Serializer for Ask
    """
    price = MoneyField(required=False, allow_null=True,)
    limit_price = MoneyField(required=False, allow_null=True,)

    class Meta:
        model = Ask

        fields = ('id','exchange_type','order_time','project','quantity','price','order_type','limit_price','ask_by')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('quantity') and attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity.') 
        elif not attrs.get('quantity') and not attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity and company.')  
        elif not attrs.get('quantity') and attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set quantity and exchange type.') 
        elif attrs.get('quantity') and not attrs.get('project') and attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set project.')
        elif attrs.get('quantity') and not attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set project and exchange type.')
        elif attrs.get('quantity') and attrs.get('project') and not attrs.get('exchange_type'):
            raise serializers.ValidationError('Please set exchange type.')
        elif attrs.get('order_type') == 'limit' and not attrs.get('limit_price'):
            raise serializers.ValidationError('Please set limit price.')
        elif attrs.get('quantity') and attrs.get('project') and attrs.get('exchange_type'):
            share_obj = UserCompanyShares.objects.filter(project=attrs.get('project'),user=self.context['request'].user).first()
            shares = 0
            if share_obj:                                                   
                if attrs.get('exchange_type') == "isx" and share_obj.isx_shares < attrs.get('quantity'):
                    raise serializers.ValidationError('You have only ' + share_obj.isx_shares + ' shares of this company in your account.')
                elif attrs.get('exchange_type') == "lsx" and share_obj.lsx_shares < attrs.get('quantity'):
                    raise serializers.ValidationError('You have only ' + share_obj.lsx_shares + ' shares of this company in your account.')      
        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        user_company_shares_obj = UserCompanyShares.objects.filter(user=self.context['request'].user,project=validated_data.get('project')).first()
        if user_company_shares_obj:
            if validated_data.get('exchange_type') == 'isx':
                user_company_shares_obj.isx_share_to_sell += validated_data.get('quantity')
                user_company_shares_obj.isx_shares -= validated_data.get('quantity')
                user_company_shares_obj.save()
            elif validated_data.get('exchange_type') == 'lsx':
                user_company_shares_obj.lsx_share_to_sell += validated_data.get('quantity')
                user_company_shares_obj.lsx_shares -= validated_data.get('quantity')
                user_company_shares_obj.save()
        return instance

class LaunchProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for Launch Project List
    """
    
    class Meta:
        model = Project

        fields = ('id','title')

