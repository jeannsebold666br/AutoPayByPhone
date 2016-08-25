# AutoPayByPhone

A simple application of python package mechanize.

Automatically use paybyphone to pay parking fee and support refeeding meters.

**Note that this program is only for educational purpose. Don't use it for any other purpose. And any responsibility or consequence caused by usage of this program is undertook by user. If you don't accept this term, then don't use this program.**

## INSTALLATION

* Import `twilio` and `mechanize` and other required libraries.
* Register an account on twilio, and obtain a free account. Then replace value of `accountId`, `authToken`, `fromNum` and `toNum` in `paybyphone.py`. (`toNum` should be your own phone number which receives notifications)
* Register two different account using two phone numbers in paybyphone, and set different cards in each account. (In most cases, it only support VISA and MASTERCARD. If you use other cards, it might fail to pay regardless the meter actually can accept it or not.) 
* Replace `phoneNum` with two paybyphone accounts. (Using two accounts to refeeding meter, otherwise in area that has maximum parking hour, you won't be able to refeed more than indicated.)
* Replace `pin`, `cvv` with your account pin and cvv numbers of cards of paybyphone.



Usage:
```sh
python paybyphone.py locationNum startCard{0,1} targetTimeHour targetTimeMin [nextTimeHour nextTimeMin]
```

Options:
* `locationNum`: The location number of the meter
* `startCard`: Which account to first to use (start from 0)
* `targetTimeHour`, `targetTimeMin`: Target time to park til, e.g. [17, 00]: park until 5 p.m.
* `nextTimeHour`, `nextTimeMin`: Next payment start time

Example:
```sh
python paybyphone.py 12345678 0 17 00
```
This will pay for meter number 12345678 until 17:00, and first using the first account. (Starting paying from now or meter start time, whenever is latter)
    
```sh
python paybyphone.py 12345678 0 17 00 11 25
```

This will start paying from 11:25 or now whenever is latter. (Suitable when you already paid or you know when to park)
