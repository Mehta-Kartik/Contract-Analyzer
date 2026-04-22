import sys
# from logger import logging

def error_message_detail(error,error_details:sys):
    _,_,exc_tb=error_details.exc_info()
    file_name=exc_tb.tb_frame.f_code.co_filename
    error_message="Error occured in python script named {0} line number {1} Error message {2}".format(
        file_name,
        exc_tb.tb_lineno,
        str(error)
    )

    return error_message

class CustomException(Exception):
    def __init__(self,error_message,error_details:sys):
        # return error_message_detail
        super().__init__(error_message)
        self.error_message=error_message_detail(error=error_message,error_details=error_details)

    def __str__(self):
        return self.error_message
    
# if __name__=="__main__":
#     logging.info("Hello from exception")
#     try:
#         a=1/0
#     except Exception as e:
#         raise CustomException(e,sys)