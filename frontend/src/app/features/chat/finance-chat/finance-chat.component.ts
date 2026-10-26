import { Component } from '@angular/core';
import { ChatUiComponent } from '../../../shared/components/chat-ui/chat-ui.component';

@Component({
  selector: 'app-finance-chat',
  standalone: true,
  imports: [ChatUiComponent],
  template: `<app-chat-ui mode="finance"></app-chat-ui>`,
  styleUrl: './finance-chat.component.css'
})
export class FinanceChatComponent {

}
