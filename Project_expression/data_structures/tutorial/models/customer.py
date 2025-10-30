from typing import Any, Dict, Type, TypeVar, Tuple, Optional, BinaryIO, TextIO, TYPE_CHECKING

from typing import List


from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import cast, List
from typing import Union
from typing import Dict
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.loan import Loan





T = TypeVar("T", bound="Customer")


@_attrs_define
class Customer:
    """ 
        Attributes:
            customer_id (Union[Unset, str]): идентификатор клиента
            loans (Union[Unset, List['Loan']]): кредиты
     """

    customer_id: Union[Unset, str] = UNSET
    loans: Union[Unset, List['Loan']] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.loan import Loan
        customer_id = self.customer_id

        loans: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.loans, Unset):
            loans = []
            for loans_item_data in self.loans:
                loans_item = loans_item_data.to_dict()
                loans.append(loans_item)




        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id
        if loans is not UNSET:
            field_dict["loans"] = loans

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.loan import Loan
        d = src_dict.copy()
        customer_id = d.pop("customer_id", UNSET)

        loans = []
        _loans = d.pop("loans", UNSET)
        for loans_item_data in (_loans or []):
            loans_item = Loan.from_dict(loans_item_data)



            loans.append(loans_item)


        customer = cls(
            customer_id=customer_id,
            loans=loans,
        )


        customer.additional_properties = d
        return customer

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
